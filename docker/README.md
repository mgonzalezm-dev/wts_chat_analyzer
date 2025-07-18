# WhatsApp Conversation Reader - Docker Deployment Guide

This directory contains all the Docker configurations and deployment files for the WhatsApp Conversation Reader application.

## Directory Structure

```
docker/
├── backend/          # Backend API Dockerfile
├── frontend/         # Frontend Dockerfile
├── nginx/           # Nginx configuration files
├── postgres/        # PostgreSQL initialization scripts
├── redis/           # Redis configuration
└── README.md        # This file
```

## Quick Start

### Development Environment

1. **Clone the repository and navigate to the project root**
   ```bash
   git clone <repository-url>
   cd whatsapp-conversation-analyzer
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost
   - API: http://localhost/api
   - API Docs: http://localhost/api/docs
   - pgAdmin: http://localhost:5050
   - Redis Commander: http://localhost:8081
   - Flower (Celery): http://localhost:5555
   - MailHog: http://localhost:8025

### Production Environment

1. **Set production environment variables**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production values
   ```

2. **Build and start production services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Docker Images

### Backend Image
- **Base**: Python 3.12-slim
- **Features**:
  - Multi-stage build for optimization
  - Non-root user execution
  - Health check endpoint
  - Pre-installed NLP models
  - Celery worker support

### Frontend Image
- **Build Stage**: Node.js 20-alpine
- **Serve Stage**: Nginx alpine
- **Features**:
  - Production-optimized build
  - Gzip compression
  - Security headers
  - SPA routing support

## Configuration Files

### Nginx Configuration
- `nginx.conf`: Main Nginx configuration
- `default.conf`: Server blocks and routing rules
- Features:
  - Rate limiting
  - Proxy configuration for API
  - WebSocket support
  - Static file caching
  - Security headers

### PostgreSQL Initialization
- `init.sql`: Database schema and initial data
- Creates:
  - Tables with proper indexes
  - User roles and permissions
  - Triggers and functions
  - Initial admin user

### Redis Configuration
- `redis.conf`: Redis server configuration
- Features:
  - Persistence (RDB + AOF)
  - Memory management
  - Security settings
  - Performance tuning

## Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/whatsapp_reader
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme

# Redis
REDIS_URL=redis://:changeme@redis:6379/0
REDIS_PASSWORD=changeme

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# API
CORS_ORIGINS=http://localhost,http://localhost:3000

# File Storage
UPLOAD_PATH=/app/uploads
EXPORT_PATH=/app/exports
```

## Volumes

### Development
- `postgres_data`: PostgreSQL data
- `redis_data`: Redis persistence
- `./backend:/app`: Backend code (hot reload)
- `./frontend:/app`: Frontend code (hot reload)
- `./uploads:/app/uploads`: User uploads
- `./exports:/app/exports`: Generated exports

### Production
- Named volumes for data persistence
- No source code mounting
- Backup volumes for data protection

## Networking

All services communicate through a custom bridge network:
- Network name: `whatsapp-network`
- Subnet: `172.20.0.0/16`

Service discovery uses Docker's internal DNS.

## Health Checks

All services include health checks:
- **API**: GET /health
- **PostgreSQL**: pg_isready
- **Redis**: redis-cli ping
- **Nginx**: GET /health

## Backup and Restore

### Backup
```bash
# Run backup script
./scripts/backup.sh

# Or use Docker
docker-compose exec postgres pg_dump -U postgres whatsapp_reader > backup.sql
```

### Restore
```bash
# Run restore script
./scripts/restore.sh

# Or use Docker
docker-compose exec -T postgres psql -U postgres < backup.sql
```

## Monitoring

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f worker
```

### Metrics
- Prometheus metrics: http://localhost/api/metrics
- Container stats: `docker stats`

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check ports
   netstat -tulpn | grep -E '(80|443|5432|6379|8000)'
   
   # Change ports in docker-compose.yml if needed
   ```

2. **Permission issues**
   ```bash
   # Fix upload/export directory permissions
   chmod -R 755 uploads/ exports/
   ```

3. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec postgres psql -U postgres -c "SELECT 1"
   ```

4. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   
   # Or use resource limits in docker-compose.yml
   ```

### Debugging

1. **Access container shell**
   ```bash
   docker-compose exec api bash
   docker-compose exec postgres psql -U postgres
   docker-compose exec redis redis-cli
   ```

2. **Check service status**
   ```bash
   docker-compose ps
   docker-compose exec api curl localhost:8000/health
   ```

3. **Reset everything**
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   ```

## Security Considerations

1. **Change default passwords** in production
2. **Use SSL/TLS certificates** for HTTPS
3. **Configure firewall rules** for exposed ports
4. **Enable Redis authentication**
5. **Use secrets management** for sensitive data
6. **Regular security updates** for base images
7. **Implement network policies** in Kubernetes

## Performance Tuning

1. **PostgreSQL**: Adjust shared_buffers, work_mem
2. **Redis**: Configure maxmemory policy
3. **Nginx**: Tune worker processes and connections
4. **API**: Scale replicas based on load
5. **Workers**: Adjust concurrency settings

## Maintenance

### Updates
```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate
```

### Cleanup
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup (WARNING: removes all data)
docker-compose down -v --rmi all
```

## Support

For issues or questions:
1. Check the logs first
2. Review environment variables
3. Ensure all services are healthy
4. Check the main documentation
5. Submit an issue on GitHub