from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for
from controllers.auth_controller import login_required
from database.connection import db_session
from models.session import AnalysisSession, FeedbackItem
from services.report_service import ReportService

report_bp = Blueprint('report', __name__, url_prefix='/report')

@report_bp.route('/<int:session_id>')
@login_required
def view_report(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        flash("Không tìm thấy phiên phân tích.", "danger")
        return redirect(url_for('analysis.list_sessions'))

    items = db_session.query(FeedbackItem).filter(FeedbackItem.session_id == session_id).all()
    items_dicts = [it.to_dict() for it in items]

    # Auto-generate if not yet generated
    if not analysis_session.report_bod:
        analysis_session.report_bod = ReportService.generate_bod_report(analysis_session.to_dict(), items_dicts)
    if not analysis_session.report_cskh:
        analysis_session.report_cskh = ReportService.generate_cskh_report(analysis_session.to_dict(), items_dicts)
    db_session.commit()

    current_style = request.args.get('style', 'bod')  # 'bod' or 'cskh'

    return render_template(
        'report/view.html',
        analysis_session=analysis_session,
        current_style=current_style,
        report_content=analysis_session.report_bod if current_style == 'bod' else analysis_session.report_cskh
    )

@report_bp.route('/generate/<int:session_id>', methods=['POST'])
@login_required
def generate_report(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        return jsonify({'error': 'Không tìm thấy phiên phân tích'}), 404

    data = request.json or {}
    style = data.get('style', 'bod')

    items = db_session.query(FeedbackItem).filter(FeedbackItem.session_id == session_id).all()
    items_dicts = [it.to_dict() for it in items]

    if style == 'bod':
        analysis_session.report_bod = ReportService.generate_bod_report(analysis_session.to_dict(), items_dicts)
        content = analysis_session.report_bod
    else:
        analysis_session.report_cskh = ReportService.generate_cskh_report(analysis_session.to_dict(), items_dicts)
        content = analysis_session.report_cskh

    db_session.commit()

    return jsonify({
        'success': True,
        'style': style,
        'report_content': content
    })

@report_bp.route('/share/<int:session_id>', methods=['POST'])
@login_required
def toggle_share(session_id):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.user_id == session['user_id']
    ).first()

    if not analysis_session:
        return jsonify({'error': 'Không tìm thấy phiên phân tích'}), 404

    data = request.json or {}
    is_public = data.get('is_public', not analysis_session.is_public)
    analysis_session.is_public = is_public
    db_session.commit()

    share_url = url_for('report.public_report', token=analysis_session.share_token, _external=True)

    return jsonify({
        'success': True,
        'is_public': analysis_session.is_public,
        'share_url': share_url,
        'message': 'Đã cập nhật trạng thái chia sẻ liên kết.'
    })

@report_bp.route('/public/<token>')
def public_report(token):
    analysis_session = db_session.query(AnalysisSession).filter(
        AnalysisSession.share_token == token
    ).first()

    if not analysis_session or not analysis_session.is_public:
        return render_template('report/public_shared.html', error="Báo cáo này không tồn tại hoặc đã bị tắt chia sẻ công khai.")

    current_style = request.args.get('style', 'bod')
    report_content = analysis_session.report_bod if current_style == 'bod' else analysis_session.report_cskh

    return render_template(
        'report/public_shared.html',
        analysis_session=analysis_session,
        current_style=current_style,
        report_content=report_content
    )
