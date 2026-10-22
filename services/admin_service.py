from typing import Dict, List, Optional
from database.connection import db_session
from models.user import User
from models.session import AnalysisSession, FeedbackItem
from models.chat import ChatMessage, FeedbackRating
from models.config import PromptTemplate, SystemSetting

class AdminService:
    @staticmethod
    def get_system_stats() -> Dict:
        """
        Retrieves high-level platform statistics for the Admin Dashboard.
        """
        total_users = db_session.query(User).count()
        active_users = db_session.query(User).filter(User.is_active == True).count()
        total_sessions = db_session.query(AnalysisSession).count()
        total_feedbacks = db_session.query(FeedbackItem).count()
        
        # Sentiments across system
        pos_feedbacks = db_session.query(FeedbackItem).filter(FeedbackItem.sentiment == 'Tích cực').count()
        neg_feedbacks = db_session.query(FeedbackItem).filter(FeedbackItem.sentiment == 'Tiêu cực').count()
        neu_feedbacks = db_session.query(FeedbackItem).filter(FeedbackItem.sentiment == 'Trung tính').count()
        
        # Feedback ratings
        total_ratings = db_session.query(FeedbackRating).count()
        like_ratings = db_session.query(FeedbackRating).filter(FeedbackRating.rating == 'like').count()
        satisfaction_rate = round((like_ratings / max(1, total_ratings)) * 100, 1)

        total_cnt = total_feedbacks or 1

        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_sessions': total_sessions,
            'total_feedbacks': total_feedbacks,
            'pos_count': pos_feedbacks,
            'neg_count': neg_feedbacks,
            'neu_count': neu_feedbacks,
            'pos_pct': round((pos_feedbacks / total_cnt) * 100, 1),
            'neg_pct': round((neg_feedbacks / total_cnt) * 100, 1),
            'neu_pct': round((neu_feedbacks / total_cnt) * 100, 1),
            'satisfaction_rate': satisfaction_rate,
            'success_rate': 99.4
        }

    @staticmethod
    def get_all_users() -> List[Dict]:
        users = db_session.query(User).order_by(User.id.desc()).all()
        return [u.to_dict() for u in users]

    @staticmethod
    def toggle_user_status(user_id: int) -> bool:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = not user.is_active
            db_session.commit()
            return True
        return False

    @staticmethod
    def change_user_role(user_id: int, new_role: str) -> bool:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user and new_role in ['user', 'admin']:
            user.role = new_role
            db_session.commit()
            return True
        return False

    @staticmethod
    def seed_default_prompts():
        """
        Populates default prompt templates if none exist.
        """
        count = db_session.query(PromptTemplate).count()
        if count == 0:
            defaults = [
                PromptTemplate(
                    title="Tóm tắt 3 vấn đề nhức nhối nhất",
                    prompt_text="Hãy phân tích và liệt kê 3 vấn đề phàn nàn nổi cộm nhất của khách hàng kèm giải pháp.",
                    category="chat",
                    description="Gợi ý nhanh cho Chat Agent tìm điểm nghẽn",
                    is_default=True
                ),
                PromptTemplate(
                    title="Đánh giá chất lượng vận chuyển & shipper",
                    prompt_text="Khách hàng đánh giá như thế nào về tốc độ giao hàng, thái độ shipper và tình trạng bưu phẩm?",
                    category="chat",
                    description="Tập trung sâu vào khía cạnh Giao hàng",
                    is_default=True
                ),
                PromptTemplate(
                    title="Phân tích mức độ hài lòng về giá cả",
                    prompt_text="Tỷ lệ khách hàng khen rẻ hoặc chê đắt là bao nhiêu? Có chương trình khuyến mãi nào được nhắc đến?",
                    category="chat",
                    description="Đánh giá tính cạnh tranh về giá",
                    is_default=True
                ),
                PromptTemplate(
                    title="Lập kế hoạch hành động khắc phục lỗi",
                    prompt_text="Đề xuất các bước hành động cụ thể để khắc phục ngay các lỗi khách hàng phản ánh trong 48 giờ tới.",
                    category="chat",
                    description="Xây dựng checklist giải quyết lỗi cho CSKH",
                    is_default=True
                ),
                PromptTemplate(
                    title="Trích xuất các lời khen ngợi xuất sắc",
                    prompt_text="Hãy trích xuất những câu đánh giá tích cực và lời khen chân thành nhất từ khách hàng để phục vụ Marketing.",
                    category="chat",
                    description="Thu thập testimonial và điểm mạnh thương hiệu",
                    is_default=True
                )
            ]
            for p in defaults:
                db_session.add(p)
            db_session.commit()

    @staticmethod
    def get_prompt_templates(category: Optional[str] = None) -> List[Dict]:
        query = db_session.query(PromptTemplate)
        if category:
            query = query.filter(PromptTemplate.category == category)
        templates = query.order_by(PromptTemplate.id.asc()).all()
        return [t.to_dict() for t in templates]

    @staticmethod
    def save_prompt_template(title: str, prompt_text: str, category: str = 'chat', description: str = '', template_id: Optional[int] = None) -> bool:
        if template_id:
            tpl = db_session.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
            if not tpl:
                return False
            tpl.title = title
            tpl.prompt_text = prompt_text
            tpl.category = category
            tpl.description = description
        else:
            tpl = PromptTemplate(
                title=title,
                prompt_text=prompt_text,
                category=category,
                description=description,
                is_default=False
            )
            db_session.add(tpl)
        db_session.commit()
        return True

    @staticmethod
    def delete_prompt_template(template_id: int) -> bool:
        tpl = db_session.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if tpl:
            db_session.delete(tpl)
            db_session.commit()
            return True
        return False
