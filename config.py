import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '6.626x10-34'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'web.mgkdb@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'gyrokinetic'
    MAIL_SUBJECT_PREFIX = '[MGKDB Web] '
    MAIL_SENDER = 'MGKDB Web Admin <web.mgkdb@gmail.com>'
    ADMIN = os.environ.get('ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:test@localhost/users_dev'
    MONGO_URI = "mongodb://localhost:27017/mgk_fusion"

class TestingConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:test@localhost/users_test'
    MONGO_URI = "mongodb://localhost:27017/mgk_fusion"

class ProductionConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:test@localhost/users_prod'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
