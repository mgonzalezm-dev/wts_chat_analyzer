# API Design Documentation

## Overview

The WhatsApp Conversation Reader API follows RESTful principles with a focus on consistency, security, and performance. All endpoints are versioned and require authentication except for health checks.

## Base URL Structure

```
https://api.whatsapp-reader.com/v1
```

## Authentication

All API requests (except `/health` and `/auth/login`) require JWT authentication:

```http
Authorization: Bearer <jwt_token>
```

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2025-01-17T20:41:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-01-17T20:41:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## API Endpoints

### Authentication & Authorization

#### POST /auth/login
Login with email and password
```json
// Request
{
  "email": "user@example.com",
  "password": "secure_password"
}

// Response
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "roles": ["analyst"]
    }
  }
}
```

#### POST /auth/refresh
Refresh access token
```json
// Request
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST /auth/logout
Logout and invalidate tokens

#### GET /auth/me
Get current user profile

### User Management

#### GET /users
List users (Admin only)
- Query params: `page`, `limit`, `search`, `role`, `is_active`

#### POST /users
Create new user (Admin only)
```json
{
  "email": "newuser@example.com",
  "full_name": "Jane Doe",
  "password": "secure_password",
  "roles": ["viewer"]
}
```

#### GET /users/{user_id}
Get user details

#### PATCH /users/{user_id}
Update user details

#### DELETE /users/{user_id}
Soft delete user (Admin only)

### Conversation Management

#### GET /conversations
List conversations for authenticated user
- Query params: `page`, `limit`, `search`, `date_from`, `date_to`, `status`
- Response includes pagination metadata

```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Family Group",
        "source_type": "file_upload",
        "message_count": 1523,
        "participant_count": 5,
        "started_at": "2024-01-01T00:00:00Z",
        "ended_at": "2024-12-31T23:59:59Z",
        "imported_at": "2025-01-17T10:00:00Z",
        "status": "ready"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### POST /conversations/import
Import new conversation
- Multipart form data for file upload
- Or JSON body for WhatsApp API import

```json
// For WhatsApp API import
{
  "source": "whatsapp_api",
  "api_credentials": {
    "phone_number": "+1234567890",
    "api_key": "encrypted_key"
  },
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-12-31"
  }
}
```

#### GET /conversations/{conversation_id}
Get conversation details with metadata

#### DELETE /conversations/{conversation_id}
Delete conversation (soft delete)

#### GET /conversations/{conversation_id}/messages
Get messages with pagination and filtering
- Query params: `page`, `limit`, `search`, `sender_id`, `date_from`, `date_to`, `message_type`

#### GET /conversations/{conversation_id}/participants
Get conversation participants

#### GET /conversations/{conversation_id}/analytics
Get pre-computed analytics for conversation

#### POST /conversations/{conversation_id}/export
Request conversation export
```json
{
  "format": "pdf", // pdf, csv, json
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "participants": ["participant_id_1", "participant_id_2"]
  },
  "options": {
    "include_media": false,
    "include_analytics": true
  }
}
```

### Search & Filtering

#### POST /search
Advanced search across conversations
```json
{
  "query": "meeting tomorrow",
  "filters": {
    "conversation_ids": ["id1", "id2"],
    "date_range": {
      "from": "2024-01-01",
      "to": "2024-12-31"
    },
    "participants": ["phone1", "phone2"],
    "message_types": ["text", "image"],
    "sentiment": "positive"
  },
  "options": {
    "highlight": true,
    "context_lines": 2
  }
}
```

### Analytics

#### GET /analytics/dashboard
Get dashboard statistics for user's conversations
- Query params: `date_from`, `date_to`, `conversation_ids[]`

#### POST /analytics/generate
Trigger analytics generation for specific conversations
```json
{
  "conversation_ids": ["id1", "id2"],
  "metrics": ["sentiment", "keywords", "response_times", "activity_patterns"]
}
```

#### GET /analytics/jobs/{job_id}
Check analytics job status

### Bookmarks & Annotations

#### GET /bookmarks
Get user's bookmarks
- Query params: `conversation_id`, `page`, `limit`

#### POST /bookmarks
Create new bookmark
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "660e8400-e29b-41d4-a716-446655440000",
  "title": "Important decision",
  "notes": "Team agreed on new project timeline"
}
```

#### DELETE /bookmarks/{bookmark_id}
Delete bookmark

#### GET /annotations
Get annotations
- Query params: `conversation_id`, `message_id`, `category`, `tags[]`

#### POST /annotations
Create annotation
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "660e8400-e29b-41d4-a716-446655440000",
  "content": "Action item identified",
  "category": "task",
  "tags": ["urgent", "project-x"]
}
```

### AI Summary

#### POST /ai/summarize
Generate AI summary for conversation or message range
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "options": {
    "summary_type": "executive", // executive, detailed, bullet_points
    "date_range": {
      "from": "2024-01-01",
      "to": "2024-01-31"
    },
    "focus_areas": ["decisions", "action_items", "key_topics"]
  }
}
```

### System & Health

#### GET /health
Health check endpoint (no auth required)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

#### GET /system/stats
System statistics (Admin only)

## Rate Limiting

Rate limits are applied per user:
- Standard users: 100 requests/minute
- Premium users: 500 requests/minute
- File uploads: 10 per hour

Headers included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642444800
```

## Pagination

All list endpoints support pagination:
```
GET /conversations?page=2&limit=20
```

Response includes pagination metadata:
```json
{
  "pagination": {
    "page": 2,
    "limit": 20,
    "total": 145,
    "pages": 8,
    "has_next": true,
    "has_prev": true
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| AUTH_REQUIRED | Authentication required |
| AUTH_INVALID | Invalid authentication token |
| AUTH_EXPIRED | Authentication token expired |
| PERMISSION_DENIED | Insufficient permissions |
| VALIDATION_ERROR | Input validation failed |
| RESOURCE_NOT_FOUND | Requested resource not found |
| RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| SERVER_ERROR | Internal server error |
| SERVICE_UNAVAILABLE | Service temporarily unavailable |

## API Versioning

- Version included in URL path: `/v1/`, `/v2/`
- Deprecation notices via headers:
  ```http
  Sunset: Sat, 31 Dec 2025 23:59:59 GMT
  Deprecation: true
  Link: <https://api.whatsapp-reader.com/v2/docs>; rel="successor-version"
  ```

## WebSocket Endpoints

For real-time updates (future enhancement):
```
wss://api.whatsapp-reader.com/v1/ws
```

Events:
- `conversation.imported`
- `analytics.completed`
- `export.ready`