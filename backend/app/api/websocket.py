"""
WebSocket API endpoints for real-time updates
"""
import uuid
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.audit import AuditLog, AuditAction
from app.core.security import verify_token
from app.core.auth import get_current_user

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # User subscriptions: {user_id: {conversation_ids}}
        self.subscriptions: Dict[str, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept new connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.subscriptions[user_id] = set()
        
        self.active_connections[user_id][connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
    
    def disconnect(self, user_id: str, connection_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            
            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                self.active_connections.pop(user_id, None)
                self.subscriptions.pop(user_id, None)
        
        self.connection_metadata.pop(connection_id, None)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def send_user_message(self, message: dict, user_id: str):
        """Send message to all connections of a user"""
        if user_id in self.active_connections:
            disconnected = []
            
            for conn_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                except:
                    disconnected.append(conn_id)
            
            # Clean up disconnected connections
            for conn_id in disconnected:
                self.disconnect(user_id, conn_id)
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: str, exclude_user: Optional[str] = None):
        """Broadcast message to all users subscribed to a conversation"""
        for user_id, conv_ids in self.subscriptions.items():
            if conversation_id in conv_ids and user_id != exclude_user:
                await self.send_user_message(message, user_id)
    
    def subscribe_to_conversation(self, user_id: str, conversation_id: str):
        """Subscribe user to conversation updates"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].add(conversation_id)
    
    def unsubscribe_from_conversation(self, user_id: str, conversation_id: str):
        """Unsubscribe user from conversation updates"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(conversation_id)
    
    def get_user_connections_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, {}))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates
    
    Client connects with: ws://localhost:8000/api/v1/ws?token=<jwt_token>
    """
    # Verify token
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        await websocket.close(code=4003, reason="User not found")
        return
    
    # Generate connection ID
    connection_id = str(uuid.uuid4())
    
    # Connect
    await manager.connect(websocket, str(user.id), connection_id)
    
    # Log connection
    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.WEBSOCKET_CONNECTED,
        resource_type="websocket",
        metadata={"connection_id": connection_id}
    )
    db.add(audit_log)
    await db.commit()
    
    try:
        # Send initial data
        await manager.send_personal_message(
            {
                "type": "init",
                "data": {
                    "user_id": str(user.id),
                    "connection_id": connection_id,
                    "server_time": datetime.utcnow().isoformat()
                }
            },
            websocket
        )
        
        # Handle messages
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            # Process message based on type
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    websocket
                )
                
                # Update last ping time
                if connection_id in manager.connection_metadata:
                    manager.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
            
            elif message_type == "subscribe":
                # Subscribe to conversation updates
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    # Verify user has access to conversation
                    conv_result = await db.execute(
                        select(Conversation).where(
                            Conversation.id == conversation_id,
                            Conversation.owner_id == user.id,
                            Conversation.deleted_at.is_(None)
                        )
                    )
                    if conv_result.scalar_one_or_none():
                        manager.subscribe_to_conversation(str(user.id), conversation_id)
                        await manager.send_personal_message(
                            {
                                "type": "subscribed",
                                "conversation_id": conversation_id,
                                "timestamp": datetime.utcnow().isoformat()
                            },
                            websocket
                        )
                    else:
                        await manager.send_personal_message(
                            {
                                "type": "error",
                                "error": "Access denied to conversation",
                                "conversation_id": conversation_id
                            },
                            websocket
                        )
            
            elif message_type == "unsubscribe":
                # Unsubscribe from conversation updates
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    manager.unsubscribe_from_conversation(str(user.id), conversation_id)
                    await manager.send_personal_message(
                        {
                            "type": "unsubscribed",
                            "conversation_id": conversation_id,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        websocket
                    )
            
            elif message_type == "typing":
                # Broadcast typing indicator
                conversation_id = data.get("conversation_id")
                if conversation_id and conversation_id in manager.subscriptions.get(str(user.id), set()):
                    await manager.broadcast_to_conversation(
                        {
                            "type": "user_typing",
                            "conversation_id": conversation_id,
                            "user_id": str(user.id),
                            "user_name": user.full_name,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        conversation_id,
                        exclude_user=str(user.id)
                    )
            
            elif message_type == "stop_typing":
                # Broadcast stop typing
                conversation_id = data.get("conversation_id")
                if conversation_id and conversation_id in manager.subscriptions.get(str(user.id), set()):
                    await manager.broadcast_to_conversation(
                        {
                            "type": "user_stop_typing",
                            "conversation_id": conversation_id,
                            "user_id": str(user.id),
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        conversation_id,
                        exclude_user=str(user.id)
                    )
            
            else:
                # Unknown message type
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}"
                    },
                    websocket
                )
    
    except WebSocketDisconnect:
        # Clean disconnect
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Disconnect and cleanup
        manager.disconnect(str(user.id), connection_id)
        
        # Log disconnection
        try:
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.WEBSOCKET_DISCONNECTED,
                resource_type="websocket",
                metadata={"connection_id": connection_id}
            )
            db.add(audit_log)
            await db.commit()
        except:
            pass


# Helper functions for sending notifications from other parts of the app

async def notify_conversation_update(conversation_id: str, update_type: str, data: dict):
    """
    Send conversation update notification to subscribed users
    
    update_type can be: 'new_message', 'message_deleted', 'analytics_ready', etc.
    """
    await manager.broadcast_to_conversation(
        {
            "type": "conversation_update",
            "update_type": update_type,
            "conversation_id": conversation_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        },
        conversation_id
    )


async def notify_user(user_id: str, notification_type: str, data: dict):
    """
    Send notification to specific user
    
    notification_type can be: 'export_ready', 'import_complete', 'new_bookmark', etc.
    """
    await manager.send_user_message(
        {
            "type": "notification",
            "notification_type": notification_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        },
        user_id
    )


async def broadcast_system_message(message: str, level: str = "info"):
    """
    Broadcast system message to all connected users
    """
    system_message = {
        "type": "system_message",
        "level": level,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for user_id in list(manager.active_connections.keys()):
        await manager.send_user_message(system_message, user_id)


@router.get("/connections/status")
async def get_connections_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get WebSocket connections status (admin only)
    """
    if not current_user.has_permission("admin:read"):
        return {
            "success": False,
            "error": "Admin access required"
        }
    
    return {
        "success": True,
        "data": {
            "total_connections": manager.get_total_connections(),
            "total_users": len(manager.active_connections),
            "users": [
                {
                    "user_id": user_id,
                    "connections": len(connections),
                    "subscriptions": len(manager.subscriptions.get(user_id, set()))
                }
                for user_id, connections in manager.active_connections.items()
            ]
        }
    }


# Background task to clean up stale connections
async def cleanup_stale_connections():
    """
    Periodically clean up stale connections
    """
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        now = datetime.utcnow()
        stale_connections = []
        
        for conn_id, metadata in manager.connection_metadata.items():
            last_ping = metadata.get("last_ping")
            if last_ping and (now - last_ping).total_seconds() > 300:  # 5 minutes
                stale_connections.append((metadata["user_id"], conn_id))
        
        for user_id, conn_id in stale_connections:
            print(f"Cleaning up stale connection: {conn_id}")
            manager.disconnect(user_id, conn_id)


# Start cleanup task when module loads
# asyncio.create_task(cleanup_stale_connections())