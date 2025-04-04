from datetime import datetime, timedelta
from sqlalchemy import delete
from database.db import get_db
from database.models import AdminLog
import logging

logger = logging.getLogger(__name__)


async def clean_old_logs(days_to_keep: int = 90):
    """
    Удаляет логи старше указанного количества дней"""
    async for db in get_db():
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            result = await db.execute(
                delete(AdminLog).where(AdminLog.created_at < cutoff_date))
            await db.commit()

            deleted_rows = result.rowcount
            if deleted_rows > 0:
                logger.info(f"Удалено {deleted_rows} старых логов (старше {days_to_keep} дней)")
            return deleted_rows
        except Exception as e:
            logger.error(f"Ошибка при очистке логов: {e}")
            await db.rollback()
            return 0