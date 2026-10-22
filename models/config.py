from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime, timezone
from database.connection import Base

class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    prompt_text = Column(Text, nullable=False)
    category = Column(String(50), default='chat')  # 'chat', 'report_bod', 'report_cskh', 'aspect'
    description = Column(String(255), default='')
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'prompt_text': self.prompt_text,
            'category': self.category,
            'description': self.description,
            'is_default': self.is_default
        }


class SystemSetting(Base):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(Text, default='')
    description = Column(String(255), default='')

    def to_dict(self):
        return {
            'key': self.setting_key,
            'value': self.setting_value,
            'description': self.description
        }
