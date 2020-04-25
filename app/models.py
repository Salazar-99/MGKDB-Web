from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(128))
    reason = db.Column(db.String(128))
    #User must verify email address
    verified = db.Column(db.Boolean(), default=False)
    #For user approval by admin
    approved = db.Column(db.Boolean(), default=False)

    #Prevents password from being read from database
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    #Converts password to hashed string and saves it in password_hash
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    #Checks if user password is correct
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    #Creates token for email verification
    def generate_verification_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'verify': self.id}).decode('utf-8')

    #Function for confirming user using token
    def verify(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('verify') != self.id:
            return False
        self.verified = True
        db.session.add(self)
        return True
    
    #Human readable representation -
    #Each user is identified with their email for testing/debugging purposes
    def __repr__(self):
        return '<User %r>' % self.email

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
