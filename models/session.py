from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from database.connection import Base

class AnalysisSession(Base):
    __tablename__ = 'analysis_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(200), nullable=False)
    file_name = Column(String(255), default='')
    file_type = Column(String(50), default='manual')  # 'xlsx', 'csv', 'docx', 'txt', 'manual'
    
    # Counts & Metrics
    raw_count = Column(Integer, default=0)
    cleaned_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    
    # Sharing
    share_token = Column(String(64), unique=True, default=lambda: uuid.uuid4().hex)
    is_public = Column(Boolean, default=False)
    
    # Stored generated reports
    report_bod = Column(Text, default='')   # Ban Giám Đốc report
    report_cskh = Column(Text, default='')  # CSKH / Kỹ thuật report
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship('User', back_populates='sessions')
    feedback_items = relationship('FeedbackItem', back_populates='session', cascade='all, delete-orphan')
    chat_messages = relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')

    def to_dict(self):
        total = self.cleaned_count or (self.positive_count + self.negative_count + self.neutral_count) or 1
        return {
            'id': self.id,
            'title': self.title,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'raw_count': self.raw_count,
            'cleaned_count': self.cleaned_count,
            'positive_count': self.positive_count,
            'negative_count': self.negative_count,
            'neutral_count': self.neutral_count,
            'positive_pct': round((self.positive_count / total) * 100, 1),
            'negative_pct': round((self.negative_count / total) * 100, 1),
            'neutral_pct': round((self.neutral_count / total) * 100, 1),
            'avg_confidence': round(self.avg_confidence * 100, 1),
            'share_token': self.share_token,
            'is_public': self.is_public,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }


class FeedbackItem(Base):
    __tablename__ = 'feedback_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    original_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, default='')
    sentiment = Column(String(20), nullable=False)  # 'Tích cực', 'Tiêu cực', 'Trung tính'
    confidence = Column(Float, default=0.0)
    aspect = Column(String(50), default='Khác')     # 'Chất lượng', 'Giá cả', 'Dịch vụ', 'Giao hàng', 'Bao bì', 'Khác'
    aspect_sentiment = Column(String(20), default='')
    rating_star = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship('AnalysisSession', back_populates='feedback_items')

    def to_dict(self):
        return {
            'id': self.id,
            'original_text': self.original_text,
            'cleaned_text': self.cleaned_text,
            'sentiment': self.sentiment,
            'confidence': round(self.confidence * 100, 1),
            'aspect': self.aspect,
            'aspect_sentiment': self.aspect_sentiment,
            'rating_star': self.rating_star,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
