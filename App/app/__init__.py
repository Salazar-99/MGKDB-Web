from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pymongo import PyMongo
from config import config
from redis import Redis
import rq

bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()
mongo = PyMongo()

login_manager = LoginManager()
login_manager.login_view = 'main.login'

#App factory function
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    #Initializing extensions
    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    login_manager.init_app(app)
    mongo.init_app(app)
    app.redis = Redis.from_url(app.config['REDIS_URI'])
    app.task_queue = rq.Queue('mgkdb-tasks', connection=app.redis)

    #Linking views from 'main' module
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app