from .auth_controller import auth_bp
from .analysis_controller import analysis_bp
from .chat_controller import chat_bp
from .report_controller import report_bp
from .admin_controller import admin_bp

__all__ = [
    'auth_bp',
    'analysis_bp',
    'chat_bp',
    'report_bp',
    'admin_bp'
]
