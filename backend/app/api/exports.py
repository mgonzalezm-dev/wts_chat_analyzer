"""
Exports API endpoints
"""
import uuid
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.export import ExportStatus, ExportFormat, Export
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user
from app.schemas.export import (
    ExportRequest,
    ExportResponse,
    ExportStatusResponse,
    ExportListResponse,
)
from app.utils.file_storage import FileStorage

router = APIRouter()


async def process_export_job(export_id: uuid.UUID, db: AsyncSession):
    """
    Process export job in background
    """
    # Get export job
    result = await db.execute(
        select(Export).where(Export.id == export_id)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        return
    
    try:
        # Update status to processing
        export.status = ExportStatus.PROCESSING
        export.started_at = datetime.utcnow()
        await db.commit()
        
        # Get conversation and messages
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == export.conversation_id
            ).options(
                selectinload(Conversation.participants),
                selectinload(Conversation.messages).selectinload(Message.participant)
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise Exception("Conversation not found")
        
        # Apply filters from export options
        messages = conversation.messages
        options = export.options or {}
        
        if options.get('date_from'):
            date_from = datetime.fromisoformat(options['date_from'])
            messages = [m for m in messages if m.timestamp >= date_from]
        
        if options.get('date_to'):
            date_to = datetime.fromisoformat(options['date_to'])
            messages = [m for m in messages if m.timestamp <= date_to]
        
        if options.get('participant_ids'):
            participant_ids = [uuid.UUID(pid) for pid in options['participant_ids']]
            messages = [m for m in messages if m.participant_id in participant_ids]
        
        if options.get('message_types'):
            messages = [m for m in messages if m.message_type in options['message_types']]
        
        # Sort messages by timestamp
        messages.sort(key=lambda m: m.timestamp)
        
        # Generate export based on format
        file_storage = FileStorage()
        
        if export.format == ExportFormat.JSON:
            # Generate JSON export
            import json
            export_data = {
                "conversation": {
                    "id": str(conversation.id),
                    "title": conversation.title,
                    "participants": [
                        {
                            "id": str(p.id),
                            "phone_number": p.phone_number,
                            "display_name": p.display_name
                        }
                        for p in conversation.participants
                    ],
                    "message_count": len(messages),
                    "date_range": {
                        "start": min(m.timestamp for m in messages).isoformat() if messages else None,
                        "end": max(m.timestamp for m in messages).isoformat() if messages else None
                    }
                },
                "messages": [
                    {
                        "id": str(m.id),
                        "timestamp": m.timestamp.isoformat(),
                        "sender": {
                            "phone": m.participant.phone_number,
                            "name": m.participant.display_name
                        },
                        "content": m.content,
                        "type": m.message_type,
                        "media_url": m.media_url,
                        "is_deleted": m.is_deleted,
                        "is_edited": m.is_edited,
                        "reply_to_id": str(m.reply_to_id) if m.reply_to_id else None
                    }
                    for m in messages
                ]
            }
            
            file_path = await file_storage.save_export(
                json.dumps(export_data, indent=2).encode('utf-8'),
                export.id,
                'json'
            )
            
        elif export.format == ExportFormat.CSV:
            # Generate CSV export
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Timestamp', 'Sender Phone', 'Sender Name', 'Message Type',
                'Content', 'Media URL', 'Is Deleted', 'Is Edited', 'Reply To'
            ])
            
            # Write messages
            for msg in messages:
                writer.writerow([
                    msg.timestamp.isoformat(),
                    msg.participant.phone_number,
                    msg.participant.display_name or '',
                    msg.message_type,
                    msg.content,
                    msg.media_url or '',
                    'Yes' if msg.is_deleted else 'No',
                    'Yes' if msg.is_edited else 'No',
                    str(msg.reply_to_id) if msg.reply_to_id else ''
                ])
            
            file_path = await file_storage.save_export(
                output.getvalue().encode('utf-8'),
                export.id,
                'csv'
            )
            
        elif export.format == ExportFormat.TXT:
            # Generate plain text export
            lines = []
            lines.append(f"WhatsApp Conversation Export")
            lines.append(f"Conversation: {conversation.title}")
            lines.append(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append(f"Messages: {len(messages)}")
            lines.append("=" * 50)
            lines.append("")
            
            for msg in messages:
                timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                sender = msg.participant.display_name or msg.participant.phone_number
                
                if msg.is_deleted:
                    lines.append(f"[{timestamp}] {sender}: <This message was deleted>")
                else:
                    lines.append(f"[{timestamp}] {sender}: {msg.content}")
                    
                    if msg.media_url:
                        lines.append(f"  <Media: {msg.message_type}>")
                
                lines.append("")
            
            file_path = await file_storage.save_export(
                '\n'.join(lines).encode('utf-8'),
                export.id,
                'txt'
            )
            
        elif export.format == ExportFormat.PDF:
            # TODO: Implement PDF export with reportlab or similar
            raise NotImplementedError("PDF export not implemented yet")
            
        elif export.format == ExportFormat.HTML:
            # Generate HTML export
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{conversation.title} - WhatsApp Export</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #075e54; color: white; padding: 20px; }}
                    .message {{ margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; }}
                    .sender {{ font-weight: bold; color: #075e54; }}
                    .timestamp {{ color: #666; font-size: 0.9em; }}
                    .deleted {{ color: #999; font-style: italic; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{conversation.title}</h1>
                    <p>Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p>{len(messages)} messages</p>
                </div>
            """
            
            for msg in messages:
                timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                sender = msg.participant.display_name or msg.participant.phone_number
                
                html_content += f"""
                <div class="message">
                    <span class="sender">{sender}</span>
                    <span class="timestamp">{timestamp}</span>
                    <div class="content">
                """
                
                if msg.is_deleted:
                    html_content += '<span class="deleted">This message was deleted</span>'
                else:
                    html_content += msg.content.replace('\n', '<br>')
                    if msg.media_url:
                        html_content += f'<br><em>Media: {msg.message_type}</em>'
                
                html_content += """
                    </div>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            file_path = await file_storage.save_export(
                html_content.encode('utf-8'),
                export.id,
                'html'
            )
        
        else:
            raise ValueError(f"Unsupported export format: {export.format}")
        
        # Update export record
        export.status = ExportStatus.COMPLETED
        export.completed_at = datetime.utcnow()
        export.file_path = file_path
        export.file_size = os.path.getsize(file_path)
        export.total_messages = len(conversation.messages)
        export.exported_messages = len(messages)
        export.expires_at = datetime.utcnow() + timedelta(days=7)  # Expire in 7 days
        
        await db.commit()
        
    except Exception as e:
        # Update export as failed
        export.status = ExportStatus.FAILED
        export.completed_at = datetime.utcnow()
        export.error_message = str(e)
        await db.commit()


@router.post("/", response_model=ExportResponse)
async def create_export(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create new export job
    """
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == export_request.conversation_id,
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None)
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create export record
    export = Export(
        user_id=current_user.id,
        conversation_id=export_request.conversation_id,
        format=ExportFormat(export_request.format.upper()),
        status=ExportStatus.PENDING,
        options={
            "include_media": export_request.include_media,
            "include_analytics": export_request.include_analytics,
            "include_metadata": export_request.include_metadata,
            "date_from": export_request.date_from.isoformat() if export_request.date_from else None,
            "date_to": export_request.date_to.isoformat() if export_request.date_to else None,
            "participant_ids": [str(pid) for pid in export_request.participant_ids] if export_request.participant_ids else None,
            "message_types": export_request.message_types,
            "pdf_options": export_request.pdf_options
        }
    )
    db.add(export)
    
    # Log export creation
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.EXPORT_CREATED,
        resource_type="export",
        resource_id=export.id,
        metadata={
            "conversation_id": str(export_request.conversation_id),
            "format": export_request.format
        }
    )
    db.add(audit_log)
    
    await db.commit()
    
    # Queue processing job
    background_tasks.add_task(
        process_export_job,
        export.id,
        db
    )
    
    return ExportResponse(
        data={
            "export_id": str(export.id),
            "status": "pending",
            "format": export_request.format,
            "message": "Export job created successfully"
        }
    )


@router.get("/", response_model=ExportListResponse)
async def list_exports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    conversation_id: Optional[uuid.UUID] = None,
    format: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's exports
    """
    # Build query
    query = select(Export).where(
        Export.user_id == current_user.id,
        Export.deleted_at.is_(None)
    )
    
    # Apply filters
    if conversation_id:
        query = query.where(Export.conversation_id == conversation_id)
    
    if format:
        query = query.where(Export.format == ExportFormat(format.upper()))
    
    if status:
        query = query.where(Export.status == ExportStatus(status.upper()))
    
    if date_from:
        query = query.where(Export.created_at >= date_from)
    
    if date_to:
        query = query.where(Export.created_at <= date_to)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(Export.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    exports = result.scalars().all()
    
    # Format response
    return ExportListResponse(
        data={
            "exports": [
                {
                    "id": str(export.id),
                    "conversation_id": str(export.conversation_id),
                    "format": export.format.value.lower(),
                    "status": export.status.value.lower(),
                    "progress": export.progress,
                    "file_size": export.file_size,
                    "total_messages": export.total_messages,
                    "exported_messages": export.exported_messages,
                    "created_at": export.created_at,
                    "completed_at": export.completed_at,
                    "expires_at": export.expires_at,
                    "error_message": export.error_message
                }
                for export in exports
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.get("/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get export job status
    """
    # Get export
    result = await db.execute(
        select(Export).where(
            Export.id == export_id,
            Export.user_id == current_user.id,
            Export.deleted_at.is_(None)
        )
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Calculate progress
    if export.status == ExportStatus.COMPLETED:
        progress = 100
    elif export.status == ExportStatus.PROCESSING:
        # Estimate progress based on time
        if export.started_at:
            elapsed = (datetime.utcnow() - export.started_at).total_seconds()
            progress = min(int(elapsed / 60 * 100), 90)  # Max 90% until actually complete
        else:
            progress = 10
    else:
        progress = 0
    
    return ExportStatusResponse(
        id=export.id,
        conversation_id=export.conversation_id,
        format=export.format.value.lower(),
        status=export.status.value.lower(),
        progress=progress,
        file_url=f"/api/v1/exports/{export.id}/download" if export.status == ExportStatus.COMPLETED else None,
        file_size=export.file_size,
        expires_at=export.expires_at,
        total_messages=export.total_messages,
        exported_messages=export.exported_messages,
        created_at=export.created_at,
        started_at=export.started_at,
        completed_at=export.completed_at,
        error_message=export.error_message
    )


@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download exported file
    """
    # Get export
    result = await db.execute(
        select(Export).where(
            Export.id == export_id,
            Export.user_id == current_user.id,
            Export.deleted_at.is_(None)
        )
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    if export.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready. Current status: {export.status.value}"
        )
    
    if export.expires_at and export.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export has expired"
        )
    
    if not export.file_path or not os.path.exists(export.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )
    
    # Log download
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.EXPORT_DOWNLOADED,
        resource_type="export",
        resource_id=export.id
    )
    db.add(audit_log)
    await db.commit()
    
    # Get filename
    conversation_title = "conversation"
    if export.conversation_id:
        conv_result = await db.execute(
            select(Conversation.title).where(Conversation.id == export.conversation_id)
        )
        title = conv_result.scalar_one_or_none()
        if title:
            # Sanitize filename
            conversation_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    filename = f"{conversation_title}_export_{export.created_at.strftime('%Y%m%d_%H%M%S')}.{export.format.value.lower()}"
    
    return FileResponse(
        path=export.file_path,
        filename=filename,
        media_type=get_media_type(export.format)
    )


@router.delete("/{export_id}")
async def delete_export(
    export_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete export (soft delete)
    """
    # Get export
    result = await db.execute(
        select(Export).where(
            Export.id == export_id,
            Export.user_id == current_user.id,
            Export.deleted_at.is_(None)
        )
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # Soft delete
    export.deleted_at = datetime.utcnow()
    
    # Delete file if exists
    if export.file_path and os.path.exists(export.file_path):
        try:
            os.remove(export.file_path)
        except:
            pass
    
    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.EXPORT_DELETED,
        resource_type="export",
        resource_id=export.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"success": True, "message": "Export deleted successfully"}


def get_media_type(format: ExportFormat) -> str:
    """Get media type for export format"""
    mapping = {
        ExportFormat.JSON: "application/json",
        ExportFormat.CSV: "text/csv",
        ExportFormat.TXT: "text/plain",
        ExportFormat.PDF: "application/pdf",
        ExportFormat.HTML: "text/html"
    }
    return mapping.get(format, "application/octet-stream")


# Import for selectinload
from sqlalchemy.orm import selectinload