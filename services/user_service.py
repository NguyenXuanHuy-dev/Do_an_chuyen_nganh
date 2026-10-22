import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from database.connection import db_session
from models.user import User, PasswordResetToken
from models.config import SystemSetting

class UserService:
    @staticmethod
    def create_user(username: str, email: str, password: str, full_name: str = '', role: str = 'user') -> Tuple[bool, str, Optional[User]]:
        """
        Registers a new user. Checks for uniqueness of username and email.
        """
        existing_user = db_session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                return False, "Tên đăng nhập đã tồn tại trên hệ thống.", None
            return False, "Địa chỉ email đã được sử dụng.", None

        new_user = User(
            username=username,
            email=email,
            full_name=full_name or username,
            role=role,
            token_quota=50000,
            tokens_used=0,
            is_active=True
        )
        new_user.set_password(password)

        try:
            db_session.add(new_user)
            db_session.commit()
            return True, "Đăng ký tài khoản thành công!", new_user
        except Exception as e:
            db_session.rollback()
            return False, f"Lỗi tạo tài khoản: {str(e)}", None

    @staticmethod
    def authenticate(username_or_email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticates user with username/email and password.
        """
        user = db_session.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            return False, "Tài khoản hoặc mật khẩu không chính xác.", None

        if not user.is_active:
            return False, "Tài khoản này hiện đang bị tạm khóa. Vui lòng liên hệ Admin.", None

        if not user.check_password(password):
            return False, "Tài khoản hoặc mật khẩu không chính xác.", None

        return True, "Đăng nhập thành công!", user

    @staticmethod
    def google_sso_login(email: str, full_name: str = '', avatar_url: str = '') -> User:
        """
        Processes Google SSO login: finds existing user or auto-registers new Google user account.
        """
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while db_session.query(User).filter(User.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                full_name=full_name or username,
                role='user',
                token_quota=50000,
                tokens_used=0,
                is_active=True,
                avatar_url=avatar_url or f"https://api.dicebear.com/7.x/initials/svg?seed={full_name or username}"
            )
            user.set_password("google_sso_secure_" + ''.join(random.choices(string.ascii_letters, k=24)))
            db_session.add(user)
            db_session.commit()
        else:
            # Update user avatar or name if provided and not yet set
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            if full_name and not user.full_name:
                user.full_name = full_name
            db_session.commit()
        return user

    @classmethod
    def get_google_client_id(cls) -> str:
        """
        Retrieves Google Client ID from database SystemSetting or config.
        """
        from config import Config
        setting = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'google_client_id').first()
        if setting and setting.setting_value.strip():
            return setting.setting_value.strip()
        return getattr(Config, 'GOOGLE_CLIENT_ID', '').strip()

    @classmethod
    def get_google_client_secret(cls) -> str:
        """
        Retrieves Google Client Secret from database SystemSetting or config.
        """
        from config import Config
        setting = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'google_client_secret').first()
        if setting and setting.setting_value.strip():
            return setting.setting_value.strip()
        return getattr(Config, 'GOOGLE_CLIENT_SECRET', '').strip()

    @classmethod
    def set_google_oauth_credentials(cls, client_id: str, client_secret: str = '') -> bool:
        """
        Saves user-configured Google OAuth credentials into database.
        """
        setting_id = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'google_client_id').first()
        if not setting_id:
            setting_id = SystemSetting(
                setting_key='google_client_id',
                setting_value=client_id.strip(),
                description='Google OAuth 2.0 Web Client ID'
            )
            db_session.add(setting_id)
        else:
            setting_id.setting_value = client_id.strip()

        if client_secret:
            setting_sec = db_session.query(SystemSetting).filter(SystemSetting.setting_key == 'google_client_secret').first()
            if not setting_sec:
                setting_sec = SystemSetting(
                    setting_key='google_client_secret',
                    setting_value=client_secret.strip(),
                    description='Google OAuth 2.0 Client Secret'
                )
                db_session.add(setting_sec)
            else:
                setting_sec.setting_value = client_secret.strip()

        db_session.commit()
        return True

    @staticmethod
    def generate_password_reset_otp(email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generates a 6-digit OTP code for password reset.
        """
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return False, "Không tìm thấy tài khoản với email này.", None

        # Generate 6 digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        token = PasswordResetToken(
            user_id=user.id,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False
        )
        db_session.add(token)
        db_session.commit()

        # In real production, send email; in app, display OTP directly on UI for demonstration
        return True, f"Mã xác thực OTP đã được tạo: {otp_code} (Hết hạn sau 15 phút)", otp_code

    @staticmethod
    def verify_otp_and_reset_password(email: str, otp_code: str, new_password: str) -> Tuple[bool, str]:
        """
        Verifies OTP and resets user password.
        """
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return False, "Email không hợp lệ."

        token = db_session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.otp_code == otp_code,
            PasswordResetToken.is_used == False
        ).order_by(PasswordResetToken.id.desc()).first()

        if not token:
            return False, "Mã OTP không chính xác hoặc đã được sử dụng."

        now = datetime.now(timezone.utc)
        token_expires = token.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)

        if token_expires < now:
            return False, "Mã OTP đã hết hạn. Vui lòng yêu cầu mã mới."

        token.is_used = True
        user.set_password(new_password)
        db_session.commit()

        return True, "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay bây giờ."

    @staticmethod
    def deduct_tokens(user_id: int, count: int) -> bool:
        """
        Deducts tokens for text processing.
        """
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            user.tokens_used += count
            db_session.commit()
            return True
        return False
