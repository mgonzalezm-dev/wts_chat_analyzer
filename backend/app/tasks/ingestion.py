"""
Background task for processing uploaded conversation files
"""

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models.conversation import (
    Conversation, ConversationStatus, Participant, Message, MessageAttachment
)
from app.models.analytics import MessageEntity, MessageSentiment
from app.parsers import ParserFactory
from app.analytics import NLPProcessor, SentimentAnalyzer, EntityExtractor
from app.utils.file_storage import FileStorage

logger = logging.getLogger(__name__)

# Create async engine for background tasks
engine = create_async_engine(str(settings.DATABASE_URL))
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def process_conversation_file(conversation_id: str, file_path: str):
    """
    Process uploaded conversation file
    
    Args:
        conversation_id: Conversation UUID
        file_path: Path to uploaded file
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get conversation
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return
            
            # Update status to processing
            conversation.status = ConversationStatus.PROCESSING
            await db.commit()
            
            # Get file content
            file_storage = FileStorage()
            if settings.USE_S3:
                # For S3, we need to download the file first
                content = await file_storage.get_file(file_path)
                # Save to temporary file for parsing
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                # Parse file
                parser = ParserFactory.create_parser(file_path=tmp_path)
                parsed_conversation = await parser.parse_file(tmp_path)
                
                # Clean up temp file
                import os
                os.unlink(tmp_path)
            else:
                # For local storage, parse directly
                full_path = settings.UPLOAD_PATH + "/" + file_path
                parser = ParserFactory.create_parser(file_path=full_path)
                parsed_conversation = await parser.parse_file(full_path)
            
            # Process parsed data
            await process_parsed_conversation(db, conversation, parsed_conversation)
            
            # Update conversation status
            conversation.status = ConversationStatus.READY
            conversation.message_count = len(parsed_conversation.messages)
            conversation.started_at = parsed_conversation.started_at
            conversation.ended_at = parsed_conversation.ended_at
            
            # Update title if generic
            if conversation.title.startswith("Import from"):
                if len(parsed_conversation.participants) == 2:
                    other_participant = next(
                        (p for p in parsed_conversation.participants 
                         if p.display_name != parsed_conversation.participants[0].display_name),
                        None
                    )
                    if other_participant:
                        conversation.title = f"Chat with {other_participant.display_name}"
                else:
                    conversation.title = f"Group chat ({len(parsed_conversation.participants)} participants)"
            
            await db.commit()
            logger.info(f"Successfully processed conversation {conversation_id}")
            
            # Trigger analytics generation
            from analytics import generate_conversation_analytics
            await generate_conversation_analytics(conversation_id)
            
        except Exception as e:
            logger.error(f"Failed to process conversation {conversation_id}: {e}", exc_info=True)
            
            # Update conversation status to failed
            if conversation:
                conversation.status = ConversationStatus.FAILED
                conversation.metadata = conversation.metadata or {}
                conversation.metadata['error'] = str(e)
                await db.commit()


async def process_parsed_conversation(
    db: AsyncSession,
    conversation: Conversation,
    parsed_conversation
):
    """
    Process parsed conversation data and save to database
    """
    # Create participants
    participant_map = {}
    
    for parsed_participant in parsed_conversation.participants:
        participant = Participant(
            conversation_id=conversation.id,
            phone_number=parsed_participant.phone_number,
            display_name=parsed_participant.display_name,
            is_business=parsed_participant.is_business,
            metadata=parsed_participant.metadata
        )
        db.add(participant)
        await db.flush()  # Get ID
        
        # Map display name to participant for message processing
        participant_map[parsed_participant.display_name] = participant
    
    # Initialize NLP processors
    nlp_processor = NLPProcessor()
    sentiment_analyzer = SentimentAnalyzer()
    entity_extractor = EntityExtractor()
    
    # Process messages in batches
    batch_size = 100
    total_messages = len(parsed_conversation.messages)
    
    for i in range(0, total_messages, batch_size):
        batch = parsed_conversation.messages[i:i + batch_size]
        
        # Create message records
        messages = []
        for parsed_msg in batch:
            # Find participant
            participant = participant_map.get(parsed_msg.sender)
            if not participant:
                # Create system participant if not found
                participant = Participant(
                    conversation_id=conversation.id,
                    display_name=parsed_msg.sender,
                    metadata={"is_system": True}
                )
                db.add(participant)
                await db.flush()
                participant_map[parsed_msg.sender] = participant
            
            # Create message
            message = Message(
                conversation_id=conversation.id,
                sender_id=participant.id,
                message_id=parsed_msg.generate_id(),
                content=parsed_msg.content,
                message_type=parsed_msg.message_type,
                metadata=parsed_msg.metadata,
                sent_at=parsed_msg.timestamp,
                is_deleted=parsed_msg.is_deleted,
                is_edited=parsed_msg.is_edited,
                processed_at=datetime.utcnow()
            )
            db.add(message)
            messages.append(message)
            
            # Update participant stats
            if not participant.first_message_at or parsed_msg.timestamp < participant.first_message_at:
                participant.first_message_at = parsed_msg.timestamp
            if not participant.last_message_at or parsed_msg.timestamp > participant.last_message_at:
                participant.last_message_at = parsed_msg.timestamp
            participant.message_count = (participant.message_count or 0) + 1
            
            # Add attachments
            for parsed_attachment in parsed_msg.attachments:
                attachment = MessageAttachment(
                    message_id=message.id,
                    attachment_type=parsed_attachment.attachment_type,
                    file_name=parsed_attachment.filename,
                    mime_type=parsed_attachment.mime_type,
                    metadata=parsed_attachment.metadata
                )
                db.add(attachment)
        
        # Flush to get message IDs
        await db.flush()
        
        # Process NLP for batch
        if any(msg.content for msg in messages):
            # Extract entities
            entity_results = await entity_extractor.extract_entities_batch(messages)
            for msg, entities in zip(messages, entity_results.values()):
                for entity_data in entities:
                    entity = MessageEntity(
                        message_id=msg.id,
                        entity_type=entity_data['type'],
                        entity_value=entity_data['value'],
                        start_position=entity_data.get('start'),
                        end_position=entity_data.get('end'),
                        confidence_score=entity_data.get('confidence'),
                        metadata=entity_data.get('metadata', {})
                    )
                    db.add(entity)
            
            # Analyze sentiment
            sentiment_results = await sentiment_analyzer.analyze_messages_batch(messages)
            for msg, sentiment_data in zip(messages, sentiment_results):
                if sentiment_data and msg.content:
                    sentiment = MessageSentiment(
                        message_id=msg.id,
                        polarity=sentiment_data['polarity'],
                        subjectivity=sentiment_data['subjectivity'],
                        sentiment_label=sentiment_data['sentiment_label'],
                        emotion_scores=sentiment_data.get('emotion_scores', {}),
                        analyzed_at=datetime.utcnow()
                    )
                    db.add(sentiment)
        
        # Commit batch
        await db.commit()
        
        # Log progress
        progress = min(100, int((i + batch_size) / total_messages * 100))
        logger.info(f"Processing conversation {conversation.id}: {progress}% complete")