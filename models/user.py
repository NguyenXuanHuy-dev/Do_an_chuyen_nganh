from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Unicode
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.connection import Base
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Unicode(80), unique=True, nullable=False, index=True)
    email = Column(Unicode(120), unique=True, nullable=False, index=True)
    password_hash = Column(Unicode(255), nullable=False)
    full_name = Column(Unicode(150), default='')
    role = Column(Unicode(20), default='user')  # 'user' or 'admin'
    token_quota = Column(Integer, default=50000)
    tokens_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(Unicode(255), default='')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = relationship('AnalysisSession', back_populates='user', cascade='all, delete-orphan')
    chat_messages = relationship('ChatMessage', back_populates='user', cascade='all, delete-orphan')
    reset_tokens = relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'token_quota': self.token_quota,
            'tokens_used': self.tokens_used,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }


class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    otp_code = Column(Unicode(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='reset_tokens')
