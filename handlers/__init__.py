from .user import router as user_router
from .admin import router as admin_router
from .groups import router as groups_router  # Импортируем новый роутер

__all__ = ["user_router", "admin_router", "groups_router"]