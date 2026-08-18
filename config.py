import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-129381293')
    
    # MongoDB Config
    MONGO_URI = os.environ.get('MONGO_URI', None)
    
    # SQLite Config (Fallback database)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', os.path.join(BASE_DIR, 'instance', 'app.db'))
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', os.environ.get('GOOGLE_API_KEY', None))
    
    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
