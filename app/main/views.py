import os
from flask import Flask, render_template, url_for, session, redirect, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
#Dots used for relative imports
from . import main
from .forms import *
from ..email import *
from .. import db, mongo
from ..models import User

#Home page
@main.route('/')
def index():
    return render_template('index.html', logged_in=False)

#Signup page
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    #Triggers after form submission
    if form.validate_on_submit():
        #Check if email is already used
        user = User.query.filter_by(email=form.email.data).first()
        #If not, save user
        if user is None:
            #Check verify password
            if form.password.data == form.verify_password.data:
                user = User(first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            email=form.email.data,
                            password=form.password.data)
                db.session.add(user)
                db.session.commit()
                #Send email to admin account notifying of new user
                send_email('web.mgkdb@gmail.com', 'New User', 'mail/new_user_admin', user=user)
                #TODO: Implement email verification
                #send_email('user.email', 'Verify Account', '\/mail/new_user_verify', user=user)
            else:
                flash('Password verification failed, please try again')
                return redirect(url_for('.signup'))    
            return redirect(url_for('.login'))
        else:
            flash('A user with that email already exists')
            return redirect(url_for('.signup'))
    return render_template('signup.html', form=form)    

#Login page
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    #Triggers after form submission
    if form.validate_on_submit():
        #Find user
        user = User.query.filter_by(email=form.email.data).first()
        #Validate credentials
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            #Redirect to protected page user came from or default to home
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid email or password')
    return render_template('login.html', form=form)

#Logout route
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully')
    return redirect(url_for('main.index'))

#Verify route
@main.route('/verify')
def verify():
    #Change "verified" column in database to true
    return render_template('verify.html')

#Account approval route  - for use by admin
def approve():
    #Change "approved" column in database to True
    return render_template('approve.html')

#Account denial route - for use by admin
def deny():
    #Delete user from database
    
    return render_template('deny.html')

#Data page
@main.route('/data')
@login_required
def data():
    collection = mongo.db['NonlinRuns']
    #Instance of pymongo cursor class used to iterate over query results
    cursor = collection.find({})
    runs = []
    for run in cursor:
        #Getting upload time of run
        time = run['_id'].generation_time
        params = run['Parameters']
        #Converting the dictionary into a list for ease of use in template
        display_params = []
        for key, value in params.items():
            display_params.append([key,value])
        temp = {"user": run['Meta']['user'], "keywords": run['Meta']['keywords'],"time": time, "params": display_params}
        runs.append(temp)
    return render_template('data.html', runs=runs)