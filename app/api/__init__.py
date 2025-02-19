# app/api/__init__.py
# This file makes 'api' a Python package.

from .routes import router
from .controllers import chat_controller

__all__ = ["router", "chat_controller"]
