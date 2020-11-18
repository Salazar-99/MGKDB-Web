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
    
    #Human-readable representation
    def __repr__(self):
        return '<User %r>' % self.email
    
    #Start task 'name' on Redis worker
    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    #Only one task is allowed at a time
    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Class for Redis tasks
class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
