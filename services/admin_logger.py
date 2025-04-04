from datetime import datetime
from database.db import get_db
from database.models import AdminLog

async def log_admin_action(admin_id: int, action: str, details: str = None):
    """Логирует действие администратора"""
    async for db in get_db():
        try:
            log_entry = AdminLog(
                admin_id=admin_id,
                action=action,
                details=details,
                created_at=datetime.now()
            )
            db.add(log_entry)
            await db.commit()
        except Exception as e:
            print(f"Ошибка при логировании: {e}")
