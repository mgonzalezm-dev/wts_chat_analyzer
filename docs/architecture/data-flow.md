# Data Flow Documentation

## Overview

This document describes the data flow through the WhatsApp Conversation Reader system for key processes including data ingestion, processing, analytics generation, and export operations.

## 1. File Upload and Ingestion Flow

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant API
    participant Auth
    participant Storage
    participant Queue
    participant Ingestion
    participant DB
    
    User->>WebApp: Select file for upload
    WebApp->>WebApp: Validate file size/type
    WebApp->>API: POST /conversations/import
    API->>Auth: Verify JWT token
    Auth-->>API: Token valid
    
    API->>Storage: Upload file to S3
    Storage-->>API: File URL
    
    API->>DB: Create conversation record (status: importing)
    DB-->>API: Conversation ID
    
    API->>Queue: Enqueue ingestion job
    Queue-->>API: Job ID
    
    API-->>WebApp: Return job ID & status
    
    Note over Queue,Ingestion: Async Processing
    
    Queue->>Ingestion: Dequeue job
    Ingestion->>Storage: Retrieve file
    Storage-->>Ingestion: File content
    
    Ingestion->>Ingestion: Parse WhatsApp format
    Ingestion->>Ingestion: Validate data structure
    
    loop For each message batch
        Ingestion->>DB: Insert messages
        Ingestion->>DB: Update participants
    end
    
    Ingestion->>DB: Update conversation status (ready)
    Ingestion->>Queue: Trigger analytics job
```

## 2. WhatsApp Cloud API Import Flow

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant API
    participant WA_API as WhatsApp API
    participant Queue
    participant Ingestion
    participant DB
    
    User->>WebApp: Configure API import
    WebApp->>API: POST /conversations/import
    API->>DB: Store encrypted credentials
    API->>Queue: Enqueue API import job
    API-->>WebApp: Return job ID
    
    Queue->>Ingestion: Dequeue job
    Ingestion->>DB: Retrieve credentials
    
    loop Paginated requests
        Ingestion->>WA_API: GET /messages
        WA_API-->>Ingestion: Message batch
        Ingestion->>DB: Process & store messages
        Ingestion->>Ingestion: Check rate limits
    end
    
    Ingestion->>DB: Update conversation status
    Ingestion->>Queue: Trigger analytics job
```

## 3. Message Processing Pipeline

```mermaid
graph LR
    subgraph "Raw Data"
        A[Raw Messages]
    end
    
    subgraph "Text Processing"
        B[Language Detection]
        C[Tokenization]
        D[Entity Extraction]
    end
    
    subgraph "NLP Analysis"
        E[Sentiment Analysis]
        F[Keyword Extraction]
        G[Topic Modeling]
    end
    
    subgraph "Storage"
        H[(Message Table)]
        I[(Entities Table)]
        J[(Sentiment Table)]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    
    D --> I
    E --> J
    G --> H
```

### Processing Steps Detail

1. **Language Detection**
   - Detect message language using langdetect
   - Store language code with message

2. **Tokenization**
   - Split text into tokens using spaCy
   - Handle emojis and special characters

3. **Entity Extraction**
   - Extract named entities (PERSON, ORG, LOCATION, DATE)
   - Extract phone numbers, emails, URLs
   - Store with position markers

4. **Sentiment Analysis**
   - Calculate polarity (-1 to 1)
   - Calculate subjectivity (0 to 1)
   - Classify emotion categories

5. **Keyword Extraction**
   - TF-IDF for important terms
   - N-gram analysis
   - Topic clustering

## 4. Analytics Generation Flow

```mermaid
sequenceDiagram
    participant Scheduler
    participant Analytics
    participant DB
    participant Cache
    
    Note over Scheduler: Every 15 minutes
    
    Scheduler->>Analytics: Trigger batch job
    Analytics->>DB: Get unprocessed conversations
    
    loop For each conversation
        Analytics->>DB: Fetch messages
        Analytics->>Analytics: Calculate metrics
        
        Note over Analytics: Metrics calculated:<br/>- Message frequency<br/>- Response times<br/>- Active hours<br/>- Participant stats<br/>- Keyword trends<br/>- Sentiment trends
        
        Analytics->>DB: Store analytics data
        Analytics->>Cache: Update cache
    end
    
    Analytics->>Scheduler: Job complete
```

### Analytics Metrics

1. **Temporal Patterns**
   - Messages per day/hour
   - Peak activity times
   - Conversation duration

2. **Participant Metrics**
   - Message count per participant
   - Average response time
   - Initiation frequency

3. **Content Analysis**
   - Top keywords/phrases
   - Topic distribution
   - Sentiment trends over time

4. **Interaction Patterns**
   - Conversation flow
   - Question-response pairs
   - Media sharing frequency

## 5. Search and Query Flow

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant API
    participant Cache
    participant DB
    participant Search
    
    User->>WebApp: Enter search query
    WebApp->>API: POST /search
    
    API->>Cache: Check cache
    
    alt Cache hit
        Cache-->>API: Cached results
    else Cache miss
        API->>Search: Build query
        Search->>DB: Execute FTS query
        DB-->>Search: Raw results
        Search->>Search: Rank & highlight
        Search-->>API: Processed results
        API->>Cache: Store results
    end
    
    API-->>WebApp: Search results
    WebApp-->>User: Display results
```

## 6. Export Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Queue
    participant Export
    participant DB
    participant Storage
    participant Email
    
    User->>API: POST /conversations/{id}/export
    API->>Queue: Enqueue export job
    API-->>User: Job ID
    
    Queue->>Export: Dequeue job
    Export->>DB: Fetch conversation data
    
    alt PDF Export
        Export->>Export: Generate PDF
        Export->>Export: Add styling & formatting
    else CSV Export
        Export->>Export: Create CSV structure
        Export->>Export: Flatten nested data
    else JSON Export
        Export->>Export: Structure JSON
        Export->>Export: Include metadata
    end
    
    Export->>Storage: Upload file
    Storage-->>Export: File URL
    
    Export->>DB: Update job status
    Export->>Email: Send notification
    Email-->>User: Download link
```

## 7. Real-time Update Flow (Future Enhancement)

```mermaid
sequenceDiagram
    participant Service
    participant Redis
    participant WebSocket
    participant Client
    
    Service->>Redis: Publish event
    Redis->>WebSocket: Event notification
    
    loop Connected clients
        WebSocket->>WebSocket: Check permissions
        WebSocket->>Client: Send update
    end
    
    Client->>Client: Update UI
```

## Data Security Considerations

### In-Transit Security
- TLS 1.3 for all API communications
- Certificate pinning for mobile apps
- Encrypted WebSocket connections

### At-Rest Security
- AES-256 encryption for file storage
- Encrypted database fields for sensitive data
- Key rotation every 90 days

### Processing Security
- Memory encryption for NLP processing
- Secure deletion of temporary files
- Audit logging for all data access

## Performance Optimizations

### Caching Strategy
```
1. Redis Cache Layers:
   - User session data (5 min TTL)
   - Search results (15 min TTL)
   - Analytics data (15 min TTL)
   - Conversation metadata (1 hour TTL)

2. Database Query Cache:
   - Prepared statements
   - Connection pooling
   - Read replicas for analytics
```

### Batch Processing
```
1. Message Ingestion:
   - 1000 messages per batch
   - Parallel processing (4 workers)
   - Backpressure handling

2. Analytics Generation:
   - Incremental updates
   - Materialized views
   - Partitioned tables
```

### Queue Management
```
1. Priority Queues:
   - High: User exports, search
   - Medium: Analytics updates
   - Low: Batch imports

2. Dead Letter Queue:
   - Failed job retry (3 attempts)
   - Error logging
   - Manual intervention alerts