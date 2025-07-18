# WhatsApp Conversation Reader

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=flat-square&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=flat-square&logo=redis)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat-square&logo=kubernetes)

A comprehensive full-stack application for parsing, analyzing, and managing WhatsApp conversation data with advanced NLP capabilities, real-time analytics, and enterprise-grade security.

## 🚀 Key Features

### Core Functionality
- **Multi-Format Support**: Parse WhatsApp exports in .txt and JSON formats
- **Advanced Search**: Full-text search with filters for date ranges, participants, and content types
- **Real-time Analytics**: Interactive dashboards with conversation insights and statistics
- **Export Capabilities**: Generate reports in PDF, CSV, and JSON formats
- **Bookmark System**: Save and organize important messages
- **Multi-language Support**: Automatic language detection and processing

### Analytics & NLP
- **Sentiment Analysis**: Track emotional trends over time
- **Entity Extraction**: Identify people, places, organizations, and dates
- **Keyword Analysis**: Discover trending topics and frequently used terms
- **Message Statistics**: Response times, message frequency, and participation metrics
- **Media Analysis**: Track shared images, videos, and documents

### Security & Privacy
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Admin, user, and viewer roles
- **GDPR Compliance**: Data privacy controls and audit logging
- **Encrypted Storage**: Sensitive data encryption at rest
- **Rate Limiting**: API protection against abuse

## 🏗️ System Architecture

The application follows a microservices-oriented architecture with clear separation of concerns:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │     │   Mobile App    │     │   API Client    │
│   (React SPA)   │     │    (Future)     │     │  (Third-party)  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      Nginx Gateway      │
                    │   (Load Balancer/TLS)   │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
┌────────▼────────┐                             ┌────────▼────────┐
│   FastAPI App   │                             │  Static Assets  │
│  (REST API/WS)  │                             │   (Frontend)    │
└────────┬────────┘                             └─────────────────┘
         │
         ├─────────────┬─────────────┬─────────────┬─────────────┐
         │             │             │             │             │
┌────────▼────────┐ ┌──▼──────┐ ┌───▼────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  Auth Service   │ │Ingestion│ │Analytics│ │  Export   │ │  Search   │
│  (JWT/RBAC)     │ │ Service │ │ Engine  │ │  Service  │ │  Service  │
└────────┬────────┘ └──┬──────┘ └───┬────┘ └─────┬─────┘ └─────┬─────┘
         │             │             │             │             │
         └─────────────┴─────────────┴─────────────┴─────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
           ┌────────▼────────┐              ┌────────▼────────┐
           │   PostgreSQL    │              │      Redis      │
           │   (Primary DB)  │              │  (Cache/Queue)  │
           └─────────────────┘              └─────────────────┘
```

For detailed architecture documentation, see [docs/architecture/](./docs/architecture/).

## 💻 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12) - High-performance async web framework
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Cache/Queue**: Redis 7+ for caching and message queuing
- **NLP Libraries**: spaCy, NLTK, TextBlob for text analysis
- **Authentication**: JWT tokens with passlib for password hashing
- **File Storage**: Local filesystem or S3-compatible object storage

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **UI Library**: Material-UI (MUI) for consistent design
- **State Management**: Redux Toolkit for predictable state updates
- **Data Visualization**: Recharts for interactive charts
- **Form Handling**: React Hook Form with validation

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Helm charts
- **Reverse Proxy**: Nginx for load balancing and TLS termination
- **Monitoring**: Prometheus + Grafana for metrics
- **Logging**: Structured logging with correlation IDs

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.12+ (for local backend development)
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatsapp_conversation_analyzer
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/v1/docs
   - API Health Check: http://localhost:8000/health

### Local Development Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
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

5. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

## 🔧 Configuration

### Required Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/whatsapp_reader

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage (optional)
USE_S3=false
S3_BUCKET=whatsapp-uploads
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT_URL=https://s3.amazonaws.com
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/v1
VITE_WS_URL=ws://localhost:8000/v1/ws
```

## 📚 API Documentation

The API follows RESTful principles and is fully documented with OpenAPI/Swagger:

- **Interactive Documentation**: http://localhost:8000/v1/docs
- **ReDoc Documentation**: http://localhost:8000/v1/redoc

### Key Endpoints

#### Authentication
- `POST /v1/auth/register` - User registration
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh access token
- `GET /v1/auth/me` - Get current user profile

#### Conversations
- `GET /v1/conversations` - List all conversations
- `POST /v1/conversations/import` - Import new conversation
- `GET /v1/conversations/{id}` - Get conversation details
- `GET /v1/conversations/{id}/messages` - Get paginated messages
- `DELETE /v1/conversations/{id}` - Delete conversation

#### Analytics
- `GET /v1/analytics/dashboard` - Dashboard statistics
- `POST /v1/analytics/generate/{conversation_id}` - Generate analytics
- `GET /v1/analytics/{conversation_id}` - Get analytics results

#### Search & Export
- `POST /v1/search` - Advanced search across conversations
- `POST /v1/conversations/{id}/export` - Export conversation
- `GET /v1/exports/{export_id}/download` - Download export file

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_parsers.py
```

### Frontend Tests
```bash
cd frontend

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run e2e
```

## 🚢 Deployment

### Docker Deployment

1. **Build images**
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Kubernetes Deployment

1. **Install Helm chart**
   ```bash
   helm install whatsapp-reader ./kubernetes/helm/whatsapp-reader \
     --namespace whatsapp-reader \
     --create-namespace \
     --values ./kubernetes/helm/whatsapp-reader/values.yaml
   ```

2. **Check deployment status**
   ```bash
   kubectl get pods -n whatsapp-reader
   ```

### Production Considerations

- Enable TLS/SSL certificates (Let's Encrypt recommended)
- Configure proper database backups
- Set up monitoring and alerting
- Implement log aggregation
- Configure rate limiting
- Enable CORS for your domains
- Set secure headers in Nginx

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation
4. **Run tests**
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm run test
   ```
5. **Submit a pull request**
   - Provide clear description
   - Reference any related issues
   - Ensure CI passes

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint rules for TypeScript
- **Commits**: Use conventional commit messages
- **Documentation**: Update README and API docs for new features
- **Testing**: Maintain test coverage above 80%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Backend Documentation**: [backend/README.md](./backend/README.md)
- **Frontend Documentation**: [frontend/README.md](./frontend/README.md)
- **Architecture Documentation**: [docs/architecture/](./docs/architecture/)
- **API Design**: [docs/architecture/api-design.md](./docs/architecture/api-design.md)
- **Database Schema**: [docs/architecture/database-schema.md](./docs/architecture/database-schema.md)
- **Deployment Guide**: [docs/architecture/deployment.md](./docs/architecture/deployment.md)

## 🙏 Acknowledgments

- WhatsApp for providing export functionality
- The open-source community for the amazing tools and libraries
- Contributors and testers who help improve this project

---

**Note**: This project is not affiliated with or endorsed by WhatsApp or Meta Platforms, Inc.