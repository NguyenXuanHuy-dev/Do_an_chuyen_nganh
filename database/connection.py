from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from config import Config
import os

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False} if "sqlite" in Config.SQLALCHEMY_DATABASE_URI else {},
    echo=False
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models.user
    import models.session
    import models.chat
    import models.config
    Base.metadata.create_all(bind=engine)
