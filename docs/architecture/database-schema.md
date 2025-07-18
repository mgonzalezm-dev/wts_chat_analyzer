# Database Schema Design

## Overview

The PostgreSQL database schema is designed to efficiently store and query WhatsApp conversation data while maintaining data integrity, supporting analytics, and ensuring GDPR compliance.

## Schema Diagram

```mermaid
erDiagram
    users ||--o{ user_roles : has
    users ||--o{ conversations : owns
    users ||--o{ audit_logs : generates
    users ||--o{ export_jobs : requests
    
    roles ||--o{ user_roles : assigned_to
    roles ||--o{ role_permissions : has
    permissions ||--o{ role_permissions : granted_to
    
    conversations ||--o{ participants : has
    conversations ||--o{ messages : contains
    conversations ||--o{ conversation_analytics : analyzed_in
    conversations ||--o{ bookmarks : has
    conversations ||--o{ annotations : has
    
    participants ||--o{ messages : sends
    messages ||--o{ message_attachments : has
    messages ||--o{ message_entities : contains
    messages ||--o{ message_sentiment : analyzed_for
    
    analytics_jobs ||--o{ conversation_analytics : produces
    export_jobs ||--o{ export_files : generates
    
    users {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        jsonb preferences
        timestamp created_at
        timestamp updated_at
        timestamp last_login
        boolean is_active
        timestamp deleted_at
    }
    
    roles {
        uuid id PK
        string name UK
        string description
        timestamp created_at
    }
    
    permissions {
        uuid id PK
        string resource
        string action
        string description
    }
    
    user_roles {
        uuid user_id FK
        uuid role_id FK
        timestamp assigned_at
        timestamp expires_at
    }
    
    role_permissions {
        uuid role_id FK
        uuid permission_id FK
    }
    
    conversations {
        uuid id PK
        uuid owner_id FK
        string source_type
        string title
        jsonb metadata
        timestamp started_at
        timestamp ended_at
        timestamp imported_at
        bigint message_count
        string status
        timestamp deleted_at
    }
    
    participants {
        uuid id PK
        uuid conversation_id FK
        string phone_number
        string display_name
        string avatar_url
        boolean is_business
        jsonb metadata
        timestamp first_message_at
        timestamp last_message_at
        bigint message_count
    }
    
    messages {
        uuid id PK
        uuid conversation_id FK
        uuid sender_id FK
        string message_id UK
        text content
        string message_type
        jsonb metadata
        timestamp sent_at
        boolean is_deleted
        boolean is_edited
        timestamp processed_at
        tsvector search_vector
    }
    
    message_attachments {
        uuid id PK
        uuid message_id FK
        string attachment_type
        string file_name
        string storage_path
        bigint file_size
        string mime_type
        jsonb metadata
    }
    
    message_entities {
        uuid id PK
        uuid message_id FK
        string entity_type
        string entity_value
        integer start_position
        integer end_position
        float confidence_score
    }
    
    message_sentiment {
        uuid message_id PK FK
        float polarity
        float subjectivity
        string sentiment_label
        jsonb emotion_scores
        timestamp analyzed_at
    }
    
    bookmarks {
        uuid id PK
        uuid user_id FK
        uuid conversation_id FK
        uuid message_id FK
        string title
        text notes
        timestamp created_at
    }
    
    annotations {
        uuid id PK
        uuid user_id FK
        uuid conversation_id FK
        uuid message_id FK
        text content
        string category
        jsonb tags
        timestamp created_at
        timestamp updated_at
    }
    
    conversation_analytics {
        uuid id PK
        uuid conversation_id FK
        uuid job_id FK
        date analysis_date
        jsonb daily_stats
        jsonb participant_stats
        jsonb keyword_frequencies
        jsonb response_times
        jsonb sentiment_trends
        timestamp created_at
    }
    
    analytics_jobs {
        uuid id PK
        string job_type
        string status
        jsonb parameters
        timestamp scheduled_at
        timestamp started_at
        timestamp completed_at
        text error_message
    }
    
    export_jobs {
        uuid id PK
        uuid user_id FK
        uuid conversation_id FK
        string export_format
        jsonb filters
        string status
        timestamp requested_at
        timestamp completed_at
        text error_message
    }
    
    export_files {
        uuid id PK
        uuid job_id FK
        string file_name
        string storage_path
        bigint file_size
        timestamp expires_at
    }
    
    audit_logs {
        uuid id PK
        uuid user_id FK
        string action
        string resource_type
        uuid resource_id
        jsonb changes
        string ip_address
        string user_agent
        timestamp created_at
    }
```

## Table Details

### Core Tables

#### users
- Stores user account information with soft delete support
- `preferences` JSONB field for user settings (theme, language, etc.)
- Indexes: email, created_at, deleted_at

#### conversations
- Main conversation container with metadata
- `source_type`: 'file_upload', 'whatsapp_api'
- `status`: 'importing', 'processing', 'ready', 'failed'
- Indexes: owner_id, imported_at, status

#### messages
- Core message storage with full-text search support
- `search_vector` tsvector for PostgreSQL full-text search
- `message_type`: 'text', 'image', 'video', 'audio', 'document', 'location'
- Indexes: conversation_id, sender_id, sent_at, search_vector (GIN)

### Analytics Tables

#### conversation_analytics
- Pre-computed analytics data for performance
- Stores daily aggregations and trends
- Partitioned by analysis_date for efficient querying

#### message_sentiment
- NLP analysis results for individual messages
- Stores sentiment scores and emotion detection results

### Security & Compliance

#### audit_logs
- Comprehensive audit trail for GDPR compliance
- Tracks all data access and modifications
- Partitioned by created_at (monthly)

### Indexes Strategy

```sql
-- Performance indexes
CREATE INDEX idx_messages_conversation_sent ON messages(conversation_id, sent_at);
CREATE INDEX idx_messages_search ON messages USING GIN(search_vector);
CREATE INDEX idx_participants_conversation ON participants(conversation_id);
CREATE INDEX idx_analytics_conversation_date ON conversation_analytics(conversation_id, analysis_date);

-- Security indexes
CREATE INDEX idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Soft delete support
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_conversations_active ON conversations(owner_id) WHERE deleted_at IS NULL;
```

### Partitioning Strategy

1. **audit_logs**: Monthly partitions for compliance retention
2. **conversation_analytics**: Monthly partitions for performance
3. **messages**: Range partitioning by sent_at for large conversations

### Data Retention Policies

```sql
-- Automated cleanup for GDPR compliance
CREATE OR REPLACE FUNCTION cleanup_deleted_data()
RETURNS void AS $$
BEGIN
    -- Permanently delete soft-deleted users after 30 days
    DELETE FROM users 
    WHERE deleted_at IS NOT NULL 
    AND deleted_at < NOW() - INTERVAL '30 days';
    
    -- Remove old audit logs after retention period (configurable)
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Clean up expired export files
    DELETE FROM export_files 
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
```

## Migration Strategy

1. Use Alembic for schema version control
2. Always include rollback procedures
3. Test migrations on staging environment
4. Backup before production migrations
5. Monitor performance after index changes