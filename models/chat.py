from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Unicode, UnicodeText
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.connection import Base

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Unicode(20), nullable=False)  # 'user' or 'assistant'
    content = Column(UnicodeText, nullable=False)
    prompt_template = Column(Unicode(100), default='')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', back_populates='chat_messages')
    session = relationship('AnalysisSession', back_populates='chat_messages')
    ratings = relationship('FeedbackRating', back_populates='message', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'prompt_template': self.prompt_template,
            'created_at': self.created_at.strftime('%H:%M - %d/%m/%Y') if self.created_at else ''
        }


class FeedbackRating(Base):
    __tablename__ = 'feedback_ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Unicode(20), nullable=False)  # 'like', 'dislike', '5_star', etc.
    feedback_text = Column(UnicodeText, default='')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    message = relationship('ChatMessage', back_populates='ratings')

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
