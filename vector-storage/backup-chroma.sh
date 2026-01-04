#!/bin/bash
BACKUP_DIR="/path/to/backup/vector-storage"
mkdir -p $BACKUP_DIR

# Create backup of ChromaDB data
tar -czf $BACKUP_DIR/chroma-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data chroma

# Keep only last 7 days of backups
find $BACKUP_DIR -name "chroma-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $(date)"
