from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from controllers.auth_controller import admin_required
from database.connection import db_session
from models.user import User
from models.config import PromptTemplate, SystemSetting
from models.chat import FeedbackRating
from services.admin_service import AdminService
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = AdminService.get_system_stats()
    recent_users = db_session.query(User).order_by(User.id.desc()).limit(5).all()
    recent_ratings = db_session.query(FeedbackRating).order_by(FeedbackRating.id.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_users=recent_users,
        recent_ratings=recent_ratings
    )

@admin_bp.route('/users')
@admin_required
def users_list():
    users = AdminService.get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Không thể tự khóa tài khoản của chính mình!'}), 400

    success = AdminService.toggle_user_status(user_id)
    if success:
        return jsonify({'success': True, 'message': 'Đã cập nhật trạng thái người dùng.'})
    return jsonify({'error': 'Không tìm thấy người dùng'}), 404

@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@admin_required
def change_user_role(user_id):
    new_role = request.json.get('role')
    if user_id == session.get('user_id'):
        return jsonify({'error': 'Không thể tự thay đổi quyền của chính mình!'}), 400

    success = AdminService.change_user_role(user_id, new_role)
    if success:
        return jsonify({'success': True, 'message': 'Đã cập nhật phân quyền.'})
    return jsonify({'error': 'Cập nhật thất bại'}), 400

@admin_bp.route('/prompts')
@admin_required
def prompts_list():
    prompts = AdminService.get_prompt_templates()
    return render_template('admin/prompts.html', prompts=prompts)

@admin_bp.route('/prompts/save', methods=['POST'])
@admin_required
def save_prompt():
    data = request.json or {}
    template_id = data.get('id')
    title = data.get('title', '').strip()
    prompt_text = data.get('prompt_text', '').strip()
    category = data.get('category', 'chat')
    description = data.get('description', '').strip()

    if not title or not prompt_text:
        return jsonify({'error': 'Tiêu đề và nội dung prompt không được để trống.'}), 400

    success = AdminService.save_prompt_template(
        title=title,
        prompt_text=prompt_text,
        category=category,
        description=description,
        template_id=template_id
    )

    if success:
        return jsonify({'success': True, 'message': 'Lưu Prompt mẫu thành công!'})
    return jsonify({'error': 'Lỗi lưu prompt mẫu'}), 500

@admin_bp.route('/prompts/<int:template_id>/delete', methods=['POST'])
@admin_required
def delete_prompt(template_id):
    success = AdminService.delete_prompt_template(template_id)
    if success:
        return jsonify({'success': True, 'message': 'Đã xóa Prompt mẫu.'})
    return jsonify({'error': 'Không tìm thấy Prompt mẫu'}), 404

@admin_bp.route('/feedbacks')
@admin_required
def feedbacks_list():
    ratings = db_session.query(FeedbackRating).order_by(FeedbackRating.id.desc()).all()
    return render_template('admin/feedbacks.html', ratings=ratings)
