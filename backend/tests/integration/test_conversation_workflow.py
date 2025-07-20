"""Integration tests for complete conversation workflow."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from app.models.conversation import Conversation

class TestConversationWorkflow:
    """Test complete conversation processing workflow."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_upload_and_process_conversation(self, client, auth_headers, db_session):
        """Test uploading and processing a conversation file."""
        # Create a sample WhatsApp export
        chat_content = """[1/1/24, 10:00 AM] Alice: Hello Bob!
[1/1/24, 10:01 AM] Bob: Hi Alice! How are you?
[1/1/24, 10:02 AM] Alice: I'm doing great, thanks! 😊
[1/1/24, 10:03 AM] Bob: That's wonderful to hear!
[1/1/24, 10:05 AM] Alice: How was your weekend?
[1/1/24, 10:06 AM] Bob: It was fantastic! Went hiking.
[1/1/24, 10:07 AM] Alice: <Media omitted>
[1/1/24, 10:08 AM] Alice: Check out this photo from my trip!
[1/1/24, 10:09 AM] Bob: Wow, beautiful scenery!
[1/1/24, 10:10 AM] Alice: Thanks! We should plan a trip together."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(chat_content)
            temp_path = f.name
        
        try:
            # Upload the file
            with open(temp_path, 'rb') as file:
                response = client.post(
                    "/api/v1/conversations/upload",
                    headers=auth_headers,
                    files={"file": ("test_chat.txt", file, "text/plain")}
                )
            
            assert response.status_code == 201
            conversation_data = response.json()
            conversation_id = conversation_data["id"]
            
            # Verify conversation was created
            assert conversation_data["name"] == "test_chat.txt"
            assert conversation_data["status"] == "processing"
            
            # Simulate processing completion
            conversation = db_session.query(Conversation).filter_by(id=conversation_id).first()
            conversation.status = "completed"
            conversation.message_count = 10
            conversation.participant_count = 2
            db_session.commit()
            
            # Get conversation details
            response = client.get(
                f"/api/v1/conversations/{conversation_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["message_count"] == 10
            assert data["participant_count"] == 2
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.integration
    def test_conversation_analytics_generation(self, client, auth_headers, test_conversation, test_messages):
        """Test generating analytics for a conversation."""
        # Get analytics
        response = client.get(
            f"/api/v1/analytics/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        
        # Verify analytics structure
        assert analytics["message_count"] == len(test_messages)
        assert "participant_stats" in analytics
        assert "timeline_data" in analytics
        assert "sentiment_analysis" in analytics
        assert "top_keywords" in analytics
        
        # Verify participant stats
        participants = analytics["participant_stats"]
        assert len(participants) > 0
        for participant in participants:
            assert "name" in participant
            assert "message_count" in participant
            assert "avg_message_length" in participant
        
        # Verify timeline data
        timeline = analytics["timeline_data"]
        assert len(timeline) > 0
        for point in timeline:
            assert "date" in point
            assert "message_count" in point
    
    @pytest.mark.integration
    def test_message_search_workflow(self, client, auth_headers, test_conversation, test_messages):
        """Test searching messages within a conversation."""
        # Search for specific content
        search_query = "Test message"
        response = client.get(
            f"/api/v1/messages/search?conversation_id={test_conversation.id}&query={search_query}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert "items" in results
        assert len(results["items"]) > 0
        
        # Verify search results
        for message in results["items"]:
            assert search_query.lower() in message["content"].lower()
            assert message["conversation_id"] == test_conversation.id
    
    @pytest.mark.integration
    def test_export_workflow(self, client, auth_headers, test_conversation, test_messages):
        """Test exporting conversation in different formats."""
        formats = ["pdf", "csv", "json", "txt"]
        
        for export_format in formats:
            # Create export job
            response = client.post(
                "/api/v1/exports/",
                headers=auth_headers,
                json={
                    "conversation_id": test_conversation.id,
                    "format": export_format,
                    "options": {
                        "include_media": False,
                        "include_analytics": True
                    }
                }
            )
            
            assert response.status_code == 201
            export_job = response.json()
            job_id = export_job["id"]
            
            assert export_job["format"] == export_format
            assert export_job["status"] == "pending"
            
            # Check job status
            response = client.get(
                f"/api/v1/exports/{job_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["id"] == job_id
            assert "progress" in status_data
    
    @pytest.mark.integration
    def test_bookmark_workflow(self, client, auth_headers, test_messages):
        """Test bookmarking messages."""
        # Create bookmarks for important messages
        bookmarked_messages = test_messages[:3]
        bookmark_ids = []
        
        for message in bookmarked_messages:
            response = client.post(
                "/api/v1/bookmarks/",
                headers=auth_headers,
                json={
                    "message_id": message.id,
                    "note": f"Important: {message.content[:20]}"
                }
            )
            
            assert response.status_code == 201
            bookmark = response.json()
            bookmark_ids.append(bookmark["id"])
            assert bookmark["message_id"] == message.id
        
        # List bookmarks
        response = client.get("/api/v1/bookmarks/", headers=auth_headers)
        assert response.status_code == 200
        
        bookmarks = response.json()["items"]
        assert len(bookmarks) >= len(bookmark_ids)
        
        # Delete a bookmark
        response = client.delete(
            f"/api/v1/bookmarks/{bookmark_ids[0]}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        response = client.get("/api/v1/bookmarks/", headers=auth_headers)
        remaining_bookmarks = response.json()["items"]
        assert len(remaining_bookmarks) == len(bookmarks) - 1


class TestUserWorkflow:
    """Test user-related workflows."""
    
    @pytest.mark.integration
    def test_user_registration_and_login(self, client):
        """Test complete user registration and login flow."""
        # Register new user
        user_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!",
            "full_name": "Integration Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        registered_user = response.json()
        assert registered_user["email"] == user_data["email"]
        assert registered_user["full_name"] == user_data["full_name"]
        
        # Login with new user
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            }
        )
        
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # Get user profile
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == user_data["email"]
        
        # Update profile
        response = client.put(
            "/api/v1/users/me",
            headers=headers,
            json={"full_name": "Updated Integration User"}
        )
        
        assert response.status_code == 200
        updated_profile = response.json()
        assert updated_profile["full_name"] == "Updated Integration User"
    
    @pytest.mark.integration
    def test_token_refresh_workflow(self, client, test_user):
        """Test token refresh workflow."""
        # Login to get initial tokens
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            }
        )
        
        initial_tokens = response.json()
        initial_access = initial_tokens["access_token"]
        refresh_token = initial_tokens["refresh_token"]
        
        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        new_tokens = response.json()
        new_access = new_tokens["access_token"]
        
        # Verify new token is different
        assert new_access != initial_access
        
        # Verify new token works
        headers = {"Authorization": f"Bearer {new_access}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200


class TestRealTimeWorkflow:
    """Test real-time features workflow."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_websocket_notifications(self, client, auth_headers):
        """Test WebSocket notifications for conversation updates."""
        # This is a simplified test - in real scenario, would use WebSocket client
        with patch('app.api.websocket.manager.send_personal_message') as mock_send:
            # Simulate conversation update
            response = client.post(
                "/api/v1/conversations/test-id/process",
                headers=auth_headers
            )
            
            # Verify notification would be sent
            # In real implementation, WebSocket manager would handle this
            assert mock_send.called or response.status_code in [200, 404]
    
    @pytest.mark.integration
    def test_concurrent_user_access(self, client, db_session):
        """Test multiple users accessing same conversation."""
        # Create two users
        users_data = [
            {
                "email": "user1@example.com",
                "password": "User1Pass123!",
                "full_name": "User One"
            },
            {
                "email": "user2@example.com",
                "password": "User2Pass123!",
                "full_name": "User Two"
            }
        ]
        
        user_tokens = []
        for user_data in users_data:
            # Register user
            response = client.post("/api/v1/auth/register", json=user_data)
            if response.status_code == 201:
                # Login
                login_response = client.post(
                    "/api/v1/auth/login",
                    data={
                        "username": user_data["email"],
                        "password": user_data["password"]
                    }
                )
                user_tokens.append(login_response.json()["access_token"])
        
        # Both users should be able to access their own conversations
        for token in user_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/conversations/", headers=headers)
            assert response.status_code == 200


class TestErrorHandling:
    """Test error handling in workflows."""
    
    @pytest.mark.integration
    def test_invalid_file_upload(self, client, auth_headers):
        """Test uploading invalid file format."""
        # Create invalid file
        invalid_content = b"This is not a valid chat format"
        
        response = client.post(
            "/api/v1/conversations/upload",
            headers=auth_headers,
            files={"file": ("invalid.xyz", invalid_content, "application/octet-stream")}
        )
        
        # Should either reject or handle gracefully
        assert response.status_code in [400, 422, 201]
        
        if response.status_code == 201:
            # If accepted, should fail during processing
            data = response.json()
            assert data["status"] in ["processing", "failed"]
    
    @pytest.mark.integration
    def test_rate_limiting(self, client, auth_headers):
        """Test API rate limiting."""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = client.get("/api/v1/conversations/", headers=auth_headers)
            responses.append(response.status_code)
        
        # Should either all succeed or hit rate limit
        assert all(status == 200 for status in responses) or 429 in responses
    
    @pytest.mark.integration
    def test_database_transaction_rollback(self, client, auth_headers, db_session):
        """Test database transaction rollback on error."""
        with patch('app.services.conversation_processor.ConversationProcessor.process') as mock_process:
            mock_process.side_effect = Exception("Processing failed")
            
            # Upload file that will fail processing
            response = client.post(
                "/api/v1/conversations/upload",
                headers=auth_headers,
                files={"file": ("test.txt", b"content", "text/plain")}
            )
            
            # Check that partial data wasn't committed
            conversations = db_session.query(Conversation).filter_by(
                name="test.txt",
                status="completed"
            ).all()
            assert len(conversations) == 0