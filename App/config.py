import os
from dotenv import load_dotenv

#Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[MGKDB Web] '
    MAIL_SENDER = 'MGKDB Web Admin <web.mgkdb@gmail.com>'
    ADMIN = os.environ.get('ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    #Connects to mysql container
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    #SSH tunnel remote to localhost and connect locally
    MONGO_URI = os.environ.get('MONGO_URL')

class ProductionConfig(Config):
    DEBUG = False
    #Configure during deployment
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:test@localhost/users_prod'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
