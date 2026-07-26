import os
from dotenv import load_dotenv

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file if it exists
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Secret key for session signing
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-viva-prep-ai-2026-secure-fallback'
    
    # Database configuration - SQLite file in the application directory
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'vivaprep.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
