from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from controllers.auth_controller import login_required
from database.connection import db_session
from models.session import AnalysisSession, FeedbackItem
from models.chat import ChatMessage, FeedbackRating
from models.config import PromptTemplate
from services.chat_agent_service import ChatAgentService
from services.admin_service import AdminService

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/session/<int:session_id>')
@login_required
def chat_view(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        flash("Không tìm thấy phiên phân tích.", "danger")
        return redirect(url_for('analysis.list_sessions'))

    # Retrieve existing chat history
    messages = db_session.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.id.asc()).all()

    # Retrieve prompt templates
    prompts = AdminService.get_prompt_templates(category='chat')

    return render_template(
        'chat/agent.html',
        analysis_session=analysis_session,
        messages=messages,
        prompts=prompts
    )

@chat_bp.route('/api/message', methods=['POST'])
@login_required
def send_message():
    data = request.json or {}
    session_id = data.get('session_id')
    question = data.get('message', '').strip()
    prompt_template = data.get('prompt_template', '')

    if not session_id or not question:
        return jsonify({'error': 'Thiếu tham số câu hỏi hoặc mã phiên.'}), 400

    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        return jsonify({'error': 'Phiên phân tích không tồn tại.'}), 404

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=session['user_id'],
        role='user',
        content=question,
        prompt_template=prompt_template
    )
    db_session.add(user_msg)
    db_session.flush()

    # Load feedback items for this session
    items = db_session.query(FeedbackItem).filter(FeedbackItem.session_id == session_id).all()
    items_dicts = [it.to_dict() for it in items]

    # Generate answer from ChatAgentService
    answer = ChatAgentService.answer_question(
        question=question,
        session_info=analysis_session.to_dict(),
        feedback_items=items_dicts,
        prompt_template=prompt_template
    )

    # Save assistant message
    ai_msg = ChatMessage(
        session_id=session_id,
        user_id=session['user_id'],
        role='assistant',
        content=answer
    )
    db_session.add(ai_msg)
    db_session.commit()

    return jsonify({
        'success': True,
        'user_message': user_msg.to_dict(),
        'ai_message': ai_msg.to_dict()
    })

@chat_bp.route('/api/rate', methods=['POST'])
@login_required
def rate_ai_response():
    data = request.json or {}
    message_id = data.get('message_id')
    session_id = data.get('session_id')
    rating = data.get('rating')  # 'like' or 'dislike'
    feedback_text = data.get('feedback_text', '')

    if not rating:
        return jsonify({'error': 'Thiếu đánh giá rating'}), 400

    rating_entry = FeedbackRating(
        message_id=message_id,
        session_id=session_id,
        user_id=session['user_id'],
        rating=rating,
        feedback_text=feedback_text
    )
    db_session.add(rating_entry)
    db_session.commit()

    return jsonify({'success': True, 'message': 'Cảm ơn bạn đã phản hồi chất lượng câu trả lời!'})
