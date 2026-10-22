import os
import io
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from controllers.auth_controller import login_required
from services.file_service import FileService
from services.sentiment_service import SentimentService
from services.preprocess_service import PreprocessService
from services.user_service import UserService
from database.connection import db_session
from models.session import AnalysisSession, FeedbackItem
from models.user import User

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@analysis_bp.route('/')
@login_required
def index():
    user = db_session.query(User).filter(User.id == session['user_id']).first()
    recent_sessions = db_session.query(AnalysisSession).filter(
        AnalysisSession.user_id == session['user_id']
    ).order_by(AnalysisSession.id.desc()).limit(5).all()

    return render_template('analysis/index.html', user=user, recent_sessions=recent_sessions)

@analysis_bp.route('/batch')
@login_required
def batch_analysis():
    """
    Dedicated page for bulk file processing (Excel, CSV, Word, TXT) and multi-line text input.
    """
    user = db_session.query(User).filter(User.id == session['user_id']).first()
    recent_sessions = db_session.query(AnalysisSession).filter(
        AnalysisSession.user_id == session['user_id']
    ).order_by(AnalysisSession.id.desc()).limit(10).all()

    return render_template('analysis/batch.html', user=user, recent_sessions=recent_sessions)

@analysis_bp.route('/api-key', methods=['GET', 'POST'])
@login_required
def manage_api_key():
    if request.method == 'POST':
        data = request.json or {}
        api_key = data.get('api_key', '').strip()
        SentimentService.set_configured_api_key(api_key)
        return jsonify({
            'success': True,
            'message': 'Đã lưu API Key Gemini thành công!',
            'has_key': bool(api_key)
        })

    current_key = SentimentService.get_configured_api_key()
    masked = f"{current_key[:6]}...{current_key[-4:]}" if len(current_key) > 10 else ("Đã cấu hình" if current_key else "")
    return jsonify({
        'has_key': bool(current_key),
        'masked_key': masked
    })

@analysis_bp.route('/prompts-list', methods=['GET'])
@login_required
def get_prompts_list():
    return jsonify(SentimentService.PROMPT_TEMPLATES)

@analysis_bp.route('/quick-analyze', methods=['POST'])
@login_required
def quick_analyze():
    """
    Analyzes a single feedback comment using either Gemini API (with tailored Prompt) or NLP Engine.
    """
    data = request.json or {}
    text = data.get('text', '').strip() if request.is_json else request.form.get('text', '').strip()
    api_key = data.get('api_key', '').strip() or None
    prompt_mode = data.get('prompt_mode', 'general')
    custom_prompt = data.get('custom_prompt', '').strip() or None

    if not text:
        return jsonify({'error': 'Vui lòng nhập văn bản cần phân tích'}), 400

    result = SentimentService.analyze_single(
        text=text,
        api_key=api_key,
        prompt_mode=prompt_mode,
        custom_prompt=custom_prompt
    )
    UserService.deduct_tokens(session['user_id'], 1)
    return jsonify(result)

@analysis_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Handles file upload, parses content, diagnoses error rows, and returns preview data.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy tệp tải lên'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tên tệp không hợp lệ'}), 400

    if not FileService.allowed_file(file.filename):
        return jsonify({'error': 'Định dạng tệp không được hỗ trợ. Vui lòng chọn .xlsx, .xls, .csv, .docx, .txt'}), 400

    try:
        saved_path, original_name, ext = FileService.save_upload_file(file)
        raw_texts, columns = FileService.extract_texts_from_file(saved_path, ext)

        if not raw_texts:
            return jsonify({'error': 'Không tìm thấy nội dung phản hồi trong tệp'}), 400

        # Diagnose noise, blanks, duplicates
        diagnosis = FileService.preview_and_diagnose(raw_texts)
        
        # Store temporary data in user session for processing step
        session['temp_file_info'] = {
            'file_path': saved_path,
            'file_name': original_name,
            'file_type': ext,
            'raw_texts': raw_texts
        }

        return jsonify({
            'success': True,
            'file_name': original_name,
            'total_rows': diagnosis['total_raw_rows'],
            'empty_rows': diagnosis['empty_rows'],
            'duplicate_rows': diagnosis['duplicate_rows'],
            'clean_rows': diagnosis['clean_rows'],
            'noise_rate_pct': diagnosis['noise_rate_pct'],
            'preview_samples': diagnosis['preview_samples']
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi đọc tệp: {str(e)}'}), 500

@analysis_bp.route('/process', methods=['POST'])
@login_required
def process_analysis():
    """
    Executes cleaning options and runs sentiment classification batch.
    Saves results into AnalysisSession and FeedbackItems.
    """
    data = request.json or {}
    source_type = data.get('source_type', 'file')  # 'file' or 'direct_text'
    title = data.get('title', '').strip() or 'Phiên phân tích cảm xúc'
    clean_duplicates = data.get('clean_duplicates', True)
    clean_empty = data.get('clean_empty', True)

    texts_to_analyze = []
    file_name = ''
    file_type = 'manual'

    if source_type == 'file':
        temp_info = session.get('temp_file_info')
        if not temp_info or 'raw_texts' not in temp_info:
            return jsonify({'error': 'Dữ liệu tệp không tồn tại hoặc đã hết hạn phiên. Vui lòng tải lại tệp.'}), 400

        file_name = temp_info.get('file_name', '')
        file_type = temp_info.get('file_type', 'xlsx')
        raw_texts = temp_info.get('raw_texts', [])

        # Apply user's cleaning choices
        seen = set()
        for t in raw_texts:
            if t is None:
                continue
            txt = str(t).strip()
            if clean_empty and (not txt or len(txt) < 2):
                continue
            if clean_duplicates:
                lower = txt.lower()
                if lower in seen:
                    continue
                seen.add(lower)
            texts_to_analyze.append(txt)

    else:
        # Direct text input (separated by newlines)
        direct_text = data.get('direct_text', '')
        file_name = 'Nhập văn bản trực tiếp'
        file_type = 'direct_text'
        lines = [line.strip() for line in direct_text.split('\n') if line.strip()]
        texts_to_analyze = lines

    if not texts_to_analyze:
        return jsonify({'error': 'Không có dữ liệu phản hồi hợp lệ để phân tích.'}), 400

    # Execute Batch Sentiment & Aspect Analysis
    results, summary = SentimentService.analyze_batch(texts_to_analyze)

    # Save to SQLite Database
    new_session = AnalysisSession(
        user_id=session['user_id'],
        title=title,
        file_name=file_name,
        file_type=file_type,
        raw_count=len(texts_to_analyze),
        cleaned_count=len(results),
        positive_count=summary['positive_count'],
        negative_count=summary['negative_count'],
        neutral_count=summary['neutral_count'],
        avg_confidence=summary['avg_confidence']
    )
    db_session.add(new_session)
    db_session.flush()  # get new_session.id

    # Create feedback items
    for res in results:
        item = FeedbackItem(
            session_id=new_session.id,
            original_text=res['original_text'],
            cleaned_text=res['cleaned_text'],
            sentiment=res['sentiment'],
            confidence=res['confidence'],
            aspect=res['aspect'],
            aspect_sentiment=res['aspect_sentiment'],
            rating_star=res['rating_star']
        )
        db_session.add(item)

    # Deduct tokens
    UserService.deduct_tokens(session['user_id'], len(results))

    db_session.commit()

    # Clear temp session
    session.pop('temp_file_info', None)

    return jsonify({
        'success': True,
        'session_id': new_session.id,
        'redirect_url': url_for('analysis.view_session', session_id=new_session.id)
    })

@analysis_bp.route('/sessions')
@login_required
def list_sessions():
    sessions = db_session.query(AnalysisSession).filter(
        AnalysisSession.user_id == session['user_id']
    ).order_by(AnalysisSession.id.desc()).all()
    return render_template('analysis/history.html', sessions=sessions)

@analysis_bp.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        flash("Không tìm thấy phiên phân tích hoặc bạn không có quyền truy cập.", "danger")
        return redirect(url_for('analysis.list_sessions'))

    items = db_session.query(FeedbackItem).filter(
        FeedbackItem.session_id == session_id
    ).all()

    # Calculate aspect counts for charts
    aspect_counts = {}
    for it in items:
        asp = it.aspect or 'Khác'
        if asp not in aspect_counts:
            aspect_counts[asp] = {'pos': 0, 'neg': 0, 'neu': 0, 'total': 0}
        if it.sentiment == 'Tích cực': aspect_counts[asp]['pos'] += 1
        elif it.sentiment == 'Tiêu cực': aspect_counts[asp]['neg'] += 1
        else: aspect_counts[asp]['neu'] += 1
        aspect_counts[asp]['total'] += 1

    return render_template(
        'analysis/session_detail.html',
        analysis_session=analysis_session,
        items=items,
        aspect_counts=aspect_counts
    )

@analysis_bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if analysis_session:
        db_session.delete(analysis_session)
        db_session.commit()
        flash("Đã xóa phiên phân tích thành công.", "success")
    else:
        flash("Không tìm thấy phiên phân tích.", "danger")

    return redirect(url_for('analysis.list_sessions'))

@analysis_bp.route('/session/<int:session_id>/export')
@login_required
def export_session(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        flash("Không tìm thấy phiên phân tích.", "danger")
        return redirect(url_for('analysis.list_sessions'))

    items = db_session.query(FeedbackItem).filter(
        FeedbackItem.session_id == session_id
    ).all()

    records = []
    for idx, it in enumerate(items):
        records.append({
            'STT': idx + 1,
            'Văn bản gốc': it.original_text,
            'Văn bản đã làm sạch': it.cleaned_text,
            'Cảm xúc': it.sentiment,
            'Độ tin cậy (%)': round(it.confidence * 100, 1),
            'Khía cạnh': it.aspect,
            'Số sao ước tính': it.rating_star
        })

    df = pd.DataFrame(records)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Phân tích cảm xúc')
    output.seek(0)

    filename = f"Ket_qua_phan_tich_phien_{session_id}.xlsx"
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
