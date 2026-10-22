import os
import sys

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from flask import Flask, redirect, url_for, send_file, session
from config import Config
from database.connection import init_db, db_session
from controllers.auth_controller import auth_bp
from controllers.analysis_controller import analysis_bp
from controllers.chat_controller import chat_bp
from controllers.report_controller import report_bp
from controllers.admin_controller import admin_bp
from services.user_service import UserService
from services.admin_service import AdminService
from models.user import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Database Schema
    init_db()

    # Jinja template globals
    app.jinja_env.globals.update(max=max, min=min)

    # Register Blueprints (Controllers)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def root():
        if 'user_id' in session:
            return redirect(url_for('analysis.index'))
        return redirect(url_for('auth.login'))

    @app.route('/sample-data/download')
    def download_sample_data():
        sample_path = os.path.join(Config.BASE_DIR, 'sample_data', 'sample_customer_feedback.xlsx')
        if os.path.exists(sample_path):
            return send_file(
                sample_path,
                as_attachment=True,
                download_name='sample_customer_feedback.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        return "Không tìm thấy file mẫu", 404

    @app.route('/sample-data/cosmetics')
    def download_cosmetics_sample():
        sample_path = os.path.join(Config.BASE_DIR, 'sample_data', 'sample_cosmetics_launch.xlsx')
        if os.path.exists(sample_path):
            return send_file(
                sample_path,
                as_attachment=True,
                download_name='sample_cosmetics_launch.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        return "Không tìm thấy file mẫu mỹ phẩm", 404

    @app.route('/sample-data/csv')
    def download_csv_sample():
        sample_path = os.path.join(Config.BASE_DIR, 'sample_data', 'test_danh_gia_my_pham.csv')
        if os.path.exists(sample_path):
            return send_file(
                sample_path,
                as_attachment=True,
                download_name='test_danh_gia_my_pham.csv',
                mimetype='text/csv'
            )
        return "Không tìm thấy file CSV mẫu", 404

    @app.route('/sample-data/txt')
    def download_txt_sample():
        sample_path = os.path.join(Config.BASE_DIR, 'sample_data', 'test_danh_gia_my_pham.txt')
        if os.path.exists(sample_path):
            return send_file(
                sample_path,
                as_attachment=True,
                download_name='test_danh_gia_my_pham.txt',
                mimetype='text/plain'
            )
        return "Không tìm thấy file TXT mẫu", 404

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # Initial Seeds (Default Admin & Default Prompts)
    with app.app_context():
        # 1. Create Default Admin user if not exists
        admin_user = db_session.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            UserService.create_user(
                username='admin',
                email='admin@sentiment.vn',
                password='admin123',
                full_name='Quản Trị Viên Hệ Thống',
                role='admin'
            )
            print(">>> Created default admin: admin / admin123")

        # 2. Seed Default Prompts
        AdminService.seed_default_prompts()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Hệ thống phân tích cảm xúc khách hàng đang chạy tại: http://127.0.0.1:{port}\n")
    app.run(host='127.0.0.1', port=port, debug=True)
