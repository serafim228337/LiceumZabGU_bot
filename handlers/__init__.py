from .user import router as user_router
from .admin import router as admin_router
from .profile_handler import router as profile_router
from .group import router as group_router

__all__ = ['user_router', 'admin_router', 'profile_router', 'group_router']