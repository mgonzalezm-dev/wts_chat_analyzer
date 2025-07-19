# WhatsApp Conversation Reader - Backend

A comprehensive backend system for parsing, analyzing, and managing WhatsApp conversation data with advanced NLP capabilities.

## Features

- **WhatsApp File Parsing**: Support for .txt and JSON export formats
- **NLP Processing**: Sentiment analysis, entity extraction, keyword analysis
- **User Authentication**: JWT-based authentication with role-based access control
- **RESTful API**: FastAPI-based API with automatic documentation
- **Analytics Engine**: Real-time and batch analytics processing
- **Search Functionality**: Full-text search with advanced filtering
- **Export Capabilities**: Multiple export formats (PDF, CSV, JSON)
- **Security**: GDPR-compliant with comprehensive audit logging

## Technology Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **NLP**: spaCy, NLTK, TextBlob
- **Authentication**: JWT tokens with role-based access control
- **File Storage**: Local or S3-compatible storage
- **Background Tasks**: Celery (optional)

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── analytics/        # NLP and analytics modules
│   ├── core/            # Core functionality (auth, security)
│   ├── db/              # Database configuration
│   ├── models/          # SQLAlchemy models
│   ├── parsers/         # WhatsApp file parsers
│   ├── tasks/           # Background tasks
│   ├── utils/           # Utility functions
│   ├── config.py        # Application configuration
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── alembic/            # Database migrations
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLP models**
   ```bash
   python -m spacy download en_core_web_sm
   python -m nltk.downloader vader_lexicon stopwords punkt
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb whatsapp_reader
   
   # Run migrations
   alembic upgrade head
   ```

7. **Set up Redis** (optional for caching)
   ```bash
   # Install Redis or use Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key (generate a secure random key)
- `USE_S3`: Enable S3 storage (true/false)
- `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: S3 credentials

See `.env.example` for all configuration options.

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/v1/docs
- ReDoc: http://localhost:8000/v1/redoc

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## Key API Endpoints

### Authentication
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh access token
- `GET /v1/auth/me` - Get current user

### Conversations
- `GET /v1/conversations` - List conversations
- `POST /v1/conversations/import` - Import new conversation
- `GET /v1/conversations/{id}` - Get conversation details
- `GET /v1/conversations/{id}/messages` - Get messages
- `POST /v1/conversations/{id}/export` - Export conversation

### Analytics
- `GET /v1/analytics/dashboard` - Dashboard statistics
- `POST /v1/analytics/generate` - Generate analytics

### Search
- `POST /v1/search` - Advanced search

## Security Considerations

1. **Authentication**: All endpoints except health checks require JWT authentication
2. **Rate Limiting**: Configurable rate limits per user/endpoint
3. **Input Validation**: Comprehensive input validation and sanitization
4. **Audit Logging**: All data access is logged for compliance
5. **Encryption**: Sensitive data encrypted at rest and in transit

## Performance Optimization

1. **Database Indexing**: Optimized indexes for common queries
2. **Caching**: Redis caching for frequently accessed data
3. **Async Processing**: Fully async architecture for high concurrency
4. **Batch Processing**: NLP processing in batches for efficiency
5. **Connection Pooling**: Database and Redis connection pooling

## Monitoring

- Health check endpoint: `GET /health`
- Prometheus metrics: `GET /metrics`
- Structured logging with correlation IDs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Apache 2.0