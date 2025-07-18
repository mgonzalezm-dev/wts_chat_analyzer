#!/bin/bash

# WhatsApp Conversation Reader Backup Script
# This script performs backups of PostgreSQL database and uploaded files

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Database configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-whatsapp_reader}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD}"

# S3 configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups}"
AWS_PROFILE="${AWS_PROFILE:-default}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
backup_database() {
    log_info "Starting database backup..."
    
    local db_backup_file="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql.gz"
    
    # Set PGPASSWORD for pg_dump
    export PGPASSWORD="$DB_PASSWORD"
    
    # Perform database dump
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --no-owner --no-acl --clean --if-exists | gzip > "$db_backup_file"; then
        log_info "Database backup completed: $db_backup_file"
        echo "$db_backup_file"
    else
        log_error "Database backup failed!"
        return 1
    fi
    
    unset PGPASSWORD
}

# Backup uploaded files
backup_files() {
    log_info "Starting file backup..."
    
    local files_backup_file="$BACKUP_DIR/files_backup_${TIMESTAMP}.tar.gz"
    local upload_dir="${UPLOAD_DIR:-./uploads}"
    local export_dir="${EXPORT_DIR:-./exports}"
    
    if [ -d "$upload_dir" ] || [ -d "$export_dir" ]; then
        # Create tar archive of uploads and exports
        tar -czf "$files_backup_file" \
            $([ -d "$upload_dir" ] && echo "$upload_dir") \
            $([ -d "$export_dir" ] && echo "$export_dir") \
            2>/dev/null || true
        
        log_info "File backup completed: $files_backup_file"
        echo "$files_backup_file"
    else
        log_warning "No upload or export directories found to backup"
        return 0
    fi
}

# Upload to S3 (if configured)
upload_to_s3() {
    local file="$1"
    
    if [ -z "$S3_BUCKET" ]; then
        log_info "S3 backup not configured, skipping upload"
        return 0
    fi
    
    log_info "Uploading to S3: s3://$S3_BUCKET/$S3_PREFIX/$(basename "$file")"
    
    if aws s3 cp "$file" "s3://$S3_BUCKET/$S3_PREFIX/$(basename "$file")" \
        --profile "$AWS_PROFILE"; then
        log_info "S3 upload completed"
        
        # Optionally remove local file after successful upload
        if [ "${DELETE_LOCAL_AFTER_S3:-false}" = "true" ]; then
            rm -f "$file"
            log_info "Local backup file removed after S3 upload"
        fi
    else
        log_error "S3 upload failed!"
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Clean local backups
    find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Clean S3 backups if configured
    if [ -n "$S3_BUCKET" ]; then
        log_info "Cleaning up old S3 backups..."
        
        # List and delete old S3 objects
        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "$S3_PREFIX/" \
            --query "Contents[?LastModified<='$(date -d "$RETENTION_DAYS days ago" -Iseconds)'].Key" \
            --output text \
            --profile "$AWS_PROFILE" | \
        while read -r key; do
            if [ -n "$key" ] && [ "$key" != "None" ]; then
                aws s3 rm "s3://$S3_BUCKET/$key" --profile "$AWS_PROFILE"
                log_info "Deleted old S3 backup: $key"
            fi
        done
    fi
}

# Create backup metadata
create_metadata() {
    local metadata_file="$BACKUP_DIR/backup_metadata_${TIMESTAMP}.json"
    
    cat > "$metadata_file" <<EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "database": {
        "host": "$DB_HOST",
        "port": "$DB_PORT",
        "name": "$DB_NAME"
    },
    "files": {
        "upload_dir": "${UPLOAD_DIR:-./uploads}",
        "export_dir": "${EXPORT_DIR:-./exports}"
    },
    "retention_days": $RETENTION_DAYS,
    "s3_bucket": "$S3_BUCKET"
}
EOF
    
    echo "$metadata_file"
}

# Main backup process
main() {
    log_info "Starting WhatsApp Reader backup process..."
    log_info "Timestamp: $TIMESTAMP"
    
    # Check prerequisites
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump command not found. Please install PostgreSQL client."
        exit 1
    fi
    
    if [ -n "$S3_BUCKET" ] && ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found but S3 backup is configured. Please install AWS CLI."
        exit 1
    fi
    
    # Perform backups
    local db_backup_file
    local files_backup_file
    local metadata_file
    
    # Database backup
    if db_backup_file=$(backup_database); then
        [ -n "$S3_BUCKET" ] && upload_to_s3 "$db_backup_file"
    else
        log_error "Database backup failed, aborting!"
        exit 1
    fi
    
    # Files backup
    if files_backup_file=$(backup_files); then
        [ -n "$files_backup_file" ] && [ -n "$S3_BUCKET" ] && upload_to_s3 "$files_backup_file"
    fi
    
    # Create metadata
    metadata_file=$(create_metadata)
    [ -n "$S3_BUCKET" ] && upload_to_s3 "$metadata_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_info "Backup process completed successfully!"
    
    # Send notification if webhook is configured
    if [ -n "${WEBHOOK_URL:-}" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"WhatsApp Reader backup completed successfully at $TIMESTAMP\"}" \
            2>/dev/null || log_warning "Failed to send webhook notification"
    fi
}

# Run main function
main "$@"