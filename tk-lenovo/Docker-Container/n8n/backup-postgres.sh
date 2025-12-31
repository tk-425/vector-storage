#!/bin/bash
BACKUP_DIR="/home/tk-lenovo/Backup/n8n"
mkdir -p $BACKUP_DIR

# Create backup
docker exec n8n-postgres-1 pg_dump -U n8n n8n > $BACKUP_DIR/n8n-backup-$(date +%Y%m%d-%H%M%S).sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "n8n-backup-*.sql" -mtime +7 -delete

echo "Backup completed: $(date)"
