# backup.py
import shutil
import os
from datetime import datetime
from database import DB_PATH

BACKUP_DIR = 'backups'

def create_backup():
    """إنشاء نسخة احتياطية يومية."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_path = os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')
    shutil.copy2(DB_PATH, backup_path)
    print(f"تم إنشاء نسخة احتياطية: {backup_path}")

# يُستدعى تلقائيًا في main.py كل يوم (يمكن جدولة بـschedule library)
