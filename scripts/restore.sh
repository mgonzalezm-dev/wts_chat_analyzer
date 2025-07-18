#!/bin/bash

# WhatsApp Conversation Reader Restore Script
# This script restores PostgreSQL database and uploaded files from backups

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"

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
BLUE='\033[0;34m'
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

log_prompt() {
    echo -e "${BLUE}[PROMPT]${NC} $1"
}

# List available backups
list_backups() {
    log_info "Available backups:"
    echo ""
    
    # List local backups
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Local backups:"
        find "$BACKUP_DIR" -name "*.gz" -type f | sort -r | while read -r file; do
            echo "  - $(basename "$file") ($(stat -c%y "$file" 2>/dev/null || stat -f%Sm "$file"))"
        done
    fi
    
    echo ""
    
    # List S3 backups if configured
    if [ -n "$S3_BUCKET" ]; then
        log_info "S3 backups:"
        aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" --profile "$AWS_PROFILE" | \
            grep -E '\.(gz|json)$' | sort -r | head -20 | \
            while read -r line; do
                echo "  - $line"
            done
    fi
    
    echo ""
}

# Download backup from S3
download_from_s3() {
    local s3_key="$1"
    local local_file="$BACKUP_DIR/$(basename "$s3_key")"
    
    log_info "Downloading from S3: s3://$S3_BUCKET/$s3_key"
    
    mkdir -p "$BACKUP_DIR"
    
    if aws s3 cp "s3://$S3_BUCKET/$s3_key" "$local_file" --profile "$AWS_PROFILE"; then
        log_info "Download completed: $local_file"
        echo "$local_file"
    else
        log_error "S3 download failed!"
        return 1
    fi
}

# Restore database
restore_database() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring database from: $backup_file"
    
    # Confirm before proceeding
    log_warning "This will DROP and RECREATE the database: $DB_NAME"
    log_prompt "Are you sure you want to continue? (yes/no): "
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Restore cancelled by user"
        return 1
    fi
    
    # Set PGPASSWORD for psql/pg_restore
    export PGPASSWORD="$DB_PASSWORD"
    
    # Drop existing connections
    log_info "Terminating existing database connections..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
EOF
    
    # Restore database
    log_info "Restoring database..."
    if zcat "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres; then
        log_info "Database restore completed successfully!"
    else
        log_error "Database restore failed!"
        unset PGPASSWORD
        return 1
    fi
    
    unset PGPASSWORD
}

# Restore files
restore_files() {
    local backup_file="$1"
    local restore_dir="${RESTORE_DIR:-./}"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring files from: $backup_file"
    
    # Confirm before proceeding
    log_warning "This will extract files to: $restore_dir"
    log_prompt "Are you sure you want to continue? (yes/no): "
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Restore cancelled by user"
        return 1
    fi
    
    # Extract files
    log_info "Extracting files..."
    if tar -xzf "$backup_file" -C "$restore_dir"; then
        log_info "File restore completed successfully!"
        
        # Fix permissions if needed
        if [ -d "$restore_dir/uploads" ]; then
            chmod -R 755 "$restore_dir/uploads"
        fi
        if [ -d "$restore_dir/exports" ]; then
            chmod -R 755 "$restore_dir/exports"
        fi
    else
        log_error "File restore failed!"
        return 1
    fi
}

# Interactive restore menu
interactive_restore() {
    while true; do
        echo ""
        log_info "WhatsApp Reader Restore Menu"
        echo "1) List available backups"
        echo "2) Restore database from local backup"
        echo "3) Restore files from local backup"
        echo "4) Download and restore from S3"
        echo "5) Restore from specific timestamp"
        echo "6) Exit"
        echo ""
        log_prompt "Select an option (1-6): "
        read -r choice
        
        case $choice in
            1)
                list_backups
                ;;
            2)
                log_prompt "Enter database backup filename (or full path): "
                read -r db_backup
                if [ -f "$db_backup" ]; then
                    restore_database "$db_backup"
                elif [ -f "$BACKUP_DIR/$db_backup" ]; then
                    restore_database "$BACKUP_DIR/$db_backup"
                else
                    log_error "Backup file not found: $db_backup"
                fi
                ;;
            3)
                log_prompt "Enter files backup filename (or full path): "
                read -r files_backup
                if [ -f "$files_backup" ]; then
                    restore_files "$files_backup"
                elif [ -f "$BACKUP_DIR/$files_backup" ]; then
                    restore_files "$BACKUP_DIR/$files_backup"
                else
                    log_error "Backup file not found: $files_backup"
                fi
                ;;
            4)
                if [ -z "$S3_BUCKET" ]; then
                    log_error "S3 bucket not configured"
                else
                    log_prompt "Enter S3 object key (e.g., backups/db_backup_20240101_120000.sql.gz): "
                    read -r s3_key
                    if local_file=$(download_from_s3 "$s3_key"); then
                        if [[ "$s3_key" == *"db_backup"* ]]; then
                            restore_database "$local_file"
                        elif [[ "$s3_key" == *"files_backup"* ]]; then
                            restore_files "$local_file"
                        else
                            log_warning "Unknown backup type. Please choose restore type:"
                            echo "1) Database restore"
                            echo "2) Files restore"
                            log_prompt "Select (1-2): "
                            read -r restore_type
                            case $restore_type in
                                1) restore_database "$local_file" ;;
                                2) restore_files "$local_file" ;;
                                *) log_error "Invalid selection" ;;
                            esac
                        fi
                    fi
                fi
                ;;
            5)
                log_prompt "Enter timestamp (YYYYMMDD_HHMMSS): "
                read -r timestamp
                
                # Look for backups with this timestamp
                db_backup="$BACKUP_DIR/db_backup_${timestamp}.sql.gz"
                files_backup="$BACKUP_DIR/files_backup_${timestamp}.tar.gz"
                
                if [ -f "$db_backup" ] || [ -f "$files_backup" ]; then
                    [ -f "$db_backup" ] && log_info "Found database backup: $db_backup"
                    [ -f "$files_backup" ] && log_info "Found files backup: $files_backup"
                    
                    log_prompt "Restore database? (yes/no): "
                    read -r restore_db
                    [ "$restore_db" = "yes" ] && [ -f "$db_backup" ] && restore_database "$db_backup"
                    
                    log_prompt "Restore files? (yes/no): "
                    read -r restore_files_confirm
                    [ "$restore_files_confirm" = "yes" ] && [ -f "$files_backup" ] && restore_files "$files_backup"
                else
                    log_error "No backups found for timestamp: $timestamp"
                fi
                ;;
            6)
                log_info "Exiting restore utility"
                exit 0
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
    done
}

# Main function
main() {
    log_info "WhatsApp Reader Restore Utility"
    
    # Check prerequisites
    if ! command -v psql &> /dev/null; then
        log_error "psql command not found. Please install PostgreSQL client."
        exit 1
    fi
    
    if [ -n "$S3_BUCKET" ] && ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found but S3 is configured. Please install AWS CLI."
        exit 1
    fi
    
    # Check if running with arguments
    if [ $# -eq 0 ]; then
        # Interactive mode
        interactive_restore
    else
        # Command line mode
        case "$1" in
            --list|-l)
                list_backups
                ;;
            --database|-d)
                if [ -z "${2:-}" ]; then
                    log_error "Please specify backup file"
                    exit 1
                fi
                restore_database "$2"
                ;;
            --files|-f)
                if [ -z "${2:-}" ]; then
                    log_error "Please specify backup file"
                    exit 1
                fi
                restore_files "$2"
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --list, -l              List available backups"
                echo "  --database, -d FILE     Restore database from FILE"
                echo "  --files, -f FILE        Restore files from FILE"
                echo "  --help, -h              Show this help message"
                echo ""
                echo "Environment variables:"
                echo "  DB_HOST                 Database host (default: postgres)"
                echo "  DB_PORT                 Database port (default: 5432)"
                echo "  DB_NAME                 Database name (default: whatsapp_reader)"
                echo "  DB_USER                 Database user (default: postgres)"
                echo "  DB_PASSWORD             Database password (required)"
                echo "  S3_BUCKET               S3 bucket for backups (optional)"
                echo "  S3_PREFIX               S3 prefix (default: backups)"
                echo "  BACKUP_DIR              Local backup directory (default: ./backups)"
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"