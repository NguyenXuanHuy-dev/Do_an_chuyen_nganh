from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from services.user_service import UserService
from database.connection import db_session
from models.user import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Vui lòng đăng nhập để tiếp tục sử dụng hệ thống.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Vui lòng đăng nhập với tài khoản Quản trị viên.", "warning")
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash("Bạn không có quyền truy cập trang quản trị hệ thống.", "danger")
            return redirect(url_for('analysis.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('analysis.index'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')

        success, msg, user = UserService.authenticate(username_or_email, password)
        if success and user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name or user.username
            session['role'] = user.role
            flash(f"Chào mừng trở lại, {user.full_name or user.username}!", "success")
            
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('admin.dashboard') if user.role == 'admin' else url_for('analysis.index'))
        else:
            flash(msg, "danger")

    return render_template('auth/login.html', google_client_id=UserService.get_google_client_id())

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('analysis.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp.", "danger")
            return render_template('auth/register.html', google_client_id=UserService.get_google_client_id())

        if len(password) < 6:
            flash("Mật khẩu phải có độ dài tối thiểu 6 ký tự.", "danger")
            return render_template('auth/register.html', google_client_id=UserService.get_google_client_id())

        success, msg, user = UserService.create_user(username, email, password, full_name)
        if success and user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name or user.username
            session['role'] = user.role
            flash(msg, "success")
            return redirect(url_for('analysis.index'))
        else:
            flash(msg, "danger")

    return render_template('auth/register.html', google_client_id=UserService.get_google_client_id())

@auth_bp.route('/google-login')
def google_login():
    """
    Google OAuth 2.0 Login / Google SSO Endpoint.
    - If GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET are configured: Redirects to Google's official authorization endpoint.
    - If not configured: Renders the interactive Google Account Selector & Setup modal.
    """
    if 'user_id' in session:
        return redirect(url_for('analysis.index'))

    client_id = UserService.get_google_client_id()
    client_secret = UserService.get_google_client_secret()

    if client_id and client_secret:
        redirect_uri = url_for('auth.google_callback', _external=True)
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            "&access_type=offline"
            "&prompt=select_account"
        )
        return redirect(google_auth_url)

    # In Development / Sandbox mode, render the authentic Google Account Chooser & Configurator
    return render_template(
        'auth/google_picker.html', 
        google_client_id=client_id, 
        google_client_secret=client_secret
    )

@auth_bp.route('/google-token-login', methods=['POST'])
def google_token_login():
    """
    Handles Google Identity Services (GIS) One-Tap / Google Sign-In button token verification.
    Verifies the JWT ID token directly with Google's public tokeninfo API endpoint.
    """
    import requests

    credential = request.form.get('credential')
    if not credential and request.is_json:
        credential = (request.json or {}).get('credential')

    if not credential:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Thiếu mã xác thực Google (credential token).'}), 400
        flash('Không nhận được mã xác thực từ Google.', 'danger')
        return redirect(url_for('auth.login'))

    # Verify ID token using Google's public tokeninfo endpoint
    try:
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        resp = requests.get(verify_url, timeout=10)
        
        if resp.status_code != 200:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Token Google không hợp lệ hoặc đã hết hạn.'}), 400
            flash('Mã xác thực Google không hợp lệ hoặc đã hết hạn.', 'danger')
            return redirect(url_for('auth.login'))

        token_data = resp.json()
        email = token_data.get('email')
        name = token_data.get('name', '')
        picture = token_data.get('picture', '')

        if not email:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Không trích xuất được email từ tài khoản Google.'}), 400
            flash('Không thể trích xuất địa chỉ email từ tài khoản Google.', 'danger')
            return redirect(url_for('auth.login'))

        user = UserService.google_sso_login(email=email, full_name=name, avatar_url=picture)

        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name or user.username
        session['role'] = user.role
        session['avatar_url'] = user.avatar_url
        session['auth_provider'] = 'google'

        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'Đăng nhập Google thành công: {user.email}',
                'redirect_url': url_for('analysis.index')
            })

        flash(f"Đăng nhập thành công bằng tài khoản Google: {user.email}!", "success")
        return redirect(url_for('analysis.index'))

    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': f'Lỗi kết nối xác thực Google: {str(e)}'}), 500
        flash(f'Lỗi kết nối xác thực Google: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/save-google-config', methods=['POST'])
def save_google_config():
    """
    Saves Google OAuth Client ID and Secret directly from UI into database settings.
    """
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()

    if not client_id:
        flash("Vui lòng nhập Google Client ID.", "danger")
        return redirect(url_for('auth.google_login'))

    UserService.set_google_oauth_credentials(client_id, client_secret)
    flash("Đã lưu cấu hình Google OAuth 2.0 thành công! Bạn có thể sử dụng ngay tài khoản Google thật.", "success")
    return redirect(url_for('auth.google_login'))

@auth_bp.route('/google-callback')
def google_callback():
    """
    Handles Google OAuth 2.0 authorization code exchange.
    """
    import requests

    code = request.args.get('code')
    error = request.args.get('error')

    if error or not code:
        flash(f"Đăng nhập Google không thành công: {error or 'Không nhận được mã ủy quyền'}", "danger")
        return redirect(url_for('auth.login'))

    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = url_for('auth.google_callback', _external=True)

    client_id = UserService.get_google_client_id()
    client_secret = UserService.get_google_client_secret()

    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    try:
        token_resp = requests.post(token_url, data=data, timeout=10)
        token_json = token_resp.json()
        access_token = token_json.get('access_token')

        if not access_token:
            flash("Lỗi xác thực OAuth từ Google. Vui lòng thử lại.", "danger")
            return redirect(url_for('auth.login'))

        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        profile_data = userinfo_resp.json()
        email = profile_data.get('email')
        full_name = profile_data.get('name', '')
        avatar_url = profile_data.get('picture', '')

        if not email:
            flash("Không thể lấy email từ tài khoản Google của bạn.", "danger")
            return redirect(url_for('auth.login'))

        user = UserService.google_sso_login(email=email, full_name=full_name, avatar_url=avatar_url)

        session['user_id'] = user.id
        session['username'] = user.username
        session['full_name'] = user.full_name or user.username
        session['role'] = user.role
        session['avatar_url'] = user.avatar_url
        session['auth_provider'] = 'google'

        flash(f"Đăng nhập thành công với tài khoản Google: {user.email}!", "success")
        return redirect(url_for('analysis.index'))

    except Exception as e:
        flash(f"Lỗi kết nối tới dịch vụ Google OAuth: {str(e)}", "danger")
        return redirect(url_for('auth.login'))

@auth_bp.route('/google-sso-confirm', methods=['POST'])
def google_sso_confirm():
    """
    Confirms Google SSO login in Sandbox/Demo mode or custom email selection.
    """
    email = request.form.get('email', '').strip()
    full_name = request.form.get('full_name', '').strip()
    avatar_url = request.form.get('avatar_url', '').strip()

    if not email:
        flash("Vui lòng cung cấp địa chỉ email Google hợp lệ.", "danger")
        return redirect(url_for('auth.google_login'))

    if '@' not in email:
        email = f"{email}@gmail.com"

    user = UserService.google_sso_login(email=email, full_name=full_name, avatar_url=avatar_url)

    session['user_id'] = user.id
    session['username'] = user.username
    session['full_name'] = user.full_name or user.username
    session['role'] = user.role
    session['avatar_url'] = user.avatar_url
    session['auth_provider'] = 'google'

    flash(f"Đăng nhập thành công bằng tài khoản Google: {user.email}!", "success")
    return redirect(url_for('analysis.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống thành công.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    otp_generated = None
    email_entered = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        email = request.form.get('email', '').strip()
        email_entered = email

        if action == 'request_otp':
            success, msg, otp = UserService.generate_password_reset_otp(email)
            if success:
                otp_generated = otp
                flash(msg, "info")
            else:
                flash(msg, "danger")

        elif action == 'verify_reset':
            otp_code = request.form.get('otp_code', '').strip()
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            if new_password != confirm_new_password:
                flash("Mật khẩu xác nhận không trùng khớp.", "danger")
            elif len(new_password) < 6:
                flash("Mật khẩu mới phải từ 6 ký tự trở lên.", "danger")
            else:
                success, msg = UserService.verify_otp_and_reset_password(email, otp_code, new_password)
                if success:
                    flash(msg, "success")
                    return redirect(url_for('auth.login'))
                else:
                    flash(msg, "danger")

    return render_template('auth/forgot_password.html', otp_generated=otp_generated, email_entered=email_entered)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db_session.query(User).filter(User.id == session['user_id']).first()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if full_name:
            user.full_name = full_name
            session['full_name'] = full_name

        if new_password:
            if not user.check_password(current_password):
                flash("Mật khẩu hiện tại không chính xác.", "danger")
                return render_template('profile/profile.html', user=user)
            user.set_password(new_password)
            flash("Mật khẩu đã được cập nhật thành công.", "success")

        db_session.commit()
        flash("Hồ sơ tài khoản đã được lưu.", "success")

    return render_template('profile/profile.html', user=user)
