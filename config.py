import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Safely load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    env_file = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'customer_sentiment_secret_key_default')
    
    # Microsoft SQL Server (SSMS) connection parameters from environment
    DB_SERVER = os.environ.get('DB_SERVER', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'SentimentAI_DB')
    DB_DRIVER = os.environ.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
    DB_TRUSTED = os.environ.get('DB_TRUSTED_CONNECTION', 'yes')
    DB_TRUST_CERT = os.environ.get('DB_TRUST_CERT', 'yes')
    
    # Default MSSQL URI constructed dynamically
    MSSQL_URI = (
        f"mssql+pyodbc://{DB_SERVER}/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}"
        f"&trusted_connection={DB_TRUSTED}"
        f"&TrustServerCertificate={DB_TRUST_CERT}"
    )
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', MSSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'docx', 'txt'}
    
    # User token & quota
    DEFAULT_USER_TOKEN_QUOTA = 50000
    
    # AI System Config
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    AI_MODEL_NAME = os.environ.get('AI_MODEL_NAME', 'gemini-1.5-flash')
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', 0.4))
    
    # Google OAuth 2.0 Authentication (loaded securely from .env or database)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    # Session cookie configs
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
