import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SERVICE_ACCOUNT_UPLOAD_FOLDER = os.getenv('SERVICE_ACCOUNT_UPLOAD_FOLDER')
    USER_UPLOAD_FOLDER = os.getenv('USER_UPLOAD_FOLDER')
    RECIPIENT_UPLOAD_FOLDER = os.getenv('RECIPIENT_UPLOAD_FOLDER')
