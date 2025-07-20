"""Unit tests for API endpoints."""
import pytest

class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password" not in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPassword123!",
                "full_name": "Another User"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_refresh_token(self, client, test_user):
        """Test refreshing access token."""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestUserEndpoints:
    """Test user management endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_update_user_profile(self, client, test_user, auth_headers):
        """Test updating user profile."""
        response = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "email": test_user.email
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_users_admin_only(self, client, admin_auth_headers):
        """Test listing users (admin only)."""
        response = client.get("/api/v1/users/", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_users_forbidden(self, client, auth_headers):
        """Test listing users without admin rights."""
        response = client.get("/api/v1/users/", headers=auth_headers)
        
        assert response.status_code == 403


class TestConversationEndpoints:
    """Test conversation endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_upload_conversation(self, client, auth_headers):
        """Test uploading conversation file."""
        # Create a mock file
        file_content = b"[1/1/24, 10:00 AM] Alice: Test message"
        
        response = client.post(
            "/api/v1/conversations/upload",
            headers=auth_headers,
            files={"file": ("test_chat.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "test_chat.txt"
        assert data["status"] == "processing"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_conversations(self, client, auth_headers, test_conversation):
        """Test listing user conversations."""
        response = client.get("/api/v1/conversations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert any(conv["id"] == test_conversation.id for conv in data["items"])
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_conversation(self, client, auth_headers, test_conversation):
        """Test getting single conversation."""
        response = client.get(
            f"/api/v1/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_conversation.id
        assert data["name"] == test_conversation.name
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_conversation_unauthorized(self, client, test_conversation):
        """Test getting conversation without auth."""
        response = client.get(f"/api/v1/conversations/{test_conversation.id}")
        
        assert response.status_code == 401
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_conversation(self, client, auth_headers, test_conversation):
        """Test deleting conversation."""
        response = client.delete(
            f"/api/v1/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_conversation_not_found(self, client, auth_headers):
        """Test getting non-existent conversation."""
        response = client.get(
            "/api/v1/conversations/non-existent-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestMessageEndpoints:
    """Test message endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_messages(self, client, auth_headers, test_conversation, test_messages):
        """Test getting conversation messages."""
        response = client.get(
            f"/api/v1/messages/?conversation_id={test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == len(test_messages)
        assert data["total"] == len(test_messages)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_messages_with_pagination(self, client, auth_headers, test_conversation, test_messages):
        """Test getting messages with pagination."""
        response = client.get(
            f"/api/v1/messages/?conversation_id={test_conversation.id}&skip=2&limit=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == len(test_messages)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_search_messages(self, client, auth_headers, test_conversation, test_messages):
        """Test searching messages."""
        response = client.get(
            f"/api/v1/messages/search?conversation_id={test_conversation.id}&query=Test message",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert all("Test message" in msg["content"] for msg in data["items"])
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_message_by_id(self, client, auth_headers, test_messages):
        """Test getting single message."""
        message_id = test_messages[0].id
        response = client.get(
            f"/api/v1/messages/{message_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id
        assert data["content"] == test_messages[0].content


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_conversation_analytics(self, client, auth_headers, test_conversation):
        """Test getting conversation analytics."""
        response = client.get(
            f"/api/v1/analytics/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message_count" in data
        assert "participant_stats" in data
        assert "timeline_data" in data
        assert "sentiment_analysis" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_user_analytics(self, client, auth_headers):
        """Test getting user analytics."""
        response = client.get(
            "/api/v1/analytics/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_conversations" in data
        assert "total_messages" in data
        assert "active_days" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_generate_analytics_report(self, client, auth_headers, test_conversation):
        """Test generating analytics report."""
        response = client.post(
            f"/api/v1/analytics/conversations/{test_conversation.id}/report",
            headers=auth_headers,
            json={
                "report_type": "summary",
                "include_sentiment": True,
                "include_keywords": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert data["status"] == "generating"


class TestSearchEndpoints:
    """Test search endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_global_search(self, client, auth_headers, test_conversation, test_messages):
        """Test global search across conversations."""
        response = client.get(
            "/api/v1/search/?query=Test",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "messages" in data
        assert "total_results" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_advanced_search(self, client, auth_headers, test_conversation):
        """Test advanced search with filters."""
        response = client.post(
            "/api/v1/search/advanced",
            headers=auth_headers,
            json={
                "query": "Test",
                "filters": {
                    "date_from": "2024-01-01",
                    "date_to": "2024-12-31",
                    "participants": ["Alice"],
                    "message_types": ["text"]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "facets" in data


class TestBookmarkEndpoints:
    """Test bookmark endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_create_bookmark(self, client, auth_headers, test_messages):
        """Test creating bookmark."""
        response = client.post(
            "/api/v1/bookmarks/",
            headers=auth_headers,
            json={
                "message_id": test_messages[0].id,
                "note": "Important message"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message_id"] == test_messages[0].id
        assert data["note"] == "Important message"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_bookmarks(self, client, auth_headers):
        """Test listing bookmarks."""
        response = client.get("/api/v1/bookmarks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_bookmark(self, client, auth_headers, test_messages):
        """Test deleting bookmark."""
        # First create a bookmark
        create_response = client.post(
            "/api/v1/bookmarks/",
            headers=auth_headers,
            json={"message_id": test_messages[0].id}
        )
        bookmark_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(
            f"/api/v1/bookmarks/{bookmark_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204


class TestExportEndpoints:
    """Test export endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_create_export_job(self, client, auth_headers, test_conversation):
        """Test creating export job."""
        response = client.post(
            "/api/v1/exports/",
            headers=auth_headers,
            json={
                "conversation_id": test_conversation.id,
                "format": "pdf",
                "options": {
                    "include_media": False,
                    "include_analytics": True
                }
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == test_conversation.id
        assert data["format"] == "pdf"
        assert data["status"] == "pending"
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_export_status(self, client, auth_headers, test_conversation):
        """Test getting export job status."""
        # Create export job first
        create_response = client.post(
            "/api/v1/exports/",
            headers=auth_headers,
            json={
                "conversation_id": test_conversation.id,
                "format": "csv"
            }
        )
        job_id = create_response.json()["id"]
        
        # Get status
        response = client.get(
            f"/api/v1/exports/{job_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_export_jobs(self, client, auth_headers):
        """Test listing export jobs."""
        response = client.get("/api/v1/exports/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)