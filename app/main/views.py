import os
from flask import Flask, Response, render_template, url_for, session, redirect, flash, request
from flask_login import login_user, logout_user, login_required, current_user
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
        #Check if email already exists
        user = User.query.filter_by(email=form.email.data).first()
        #If not, save user
        if user is None:
            #Check verify password
            if form.password.data == form.verify_password.data:
                user = User(first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            email=form.email.data,
                            password=form.password.data,
                            role=form.role.data,
                            reason=form.reason.data)
                db.session.add(user)
                db.session.commit()
                #Generate verification token
                token = user.generate_verification_token()
                #Send email to verify account
                send_email(user.email, 'Verify Account', 'mail/new_user_verify', user=user, token=token)
                flash('A verification email has been sent to your email.')
                return redirect(url_for('main.index'))      
            else:
                flash('Password verification failed, please try again')
                return redirect(url_for('main.signup'))    
            return redirect(url_for('main.login'))
        else:
            flash('A user with that email already exists')
            return redirect(url_for('main.signup'))
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
@main.route('/verify/<token>')
@login_required
def verify(token):
    if current_user.verified:
        return redirect(url_for('main.index'))
    if current_user.verify(token):
        #Finishes off the changes made in User class verify method
        db.session.commit()
        #Sends email for admin approval following verification
        user=current_user
        send_email('web.mgkdb@gmail.com', 'New User', 'mail/new_user_admin', user=user)
        flash('Your account has been successfully verified, await admin approval for access.')
    else:
        flash('The verification link is invalid or has expired.')
    return redirect(url_for('main.index'))

#Account approval route  - for use by admin
@main.route('/approve/<email>')
def approve(email):
    #Change "approved" column in database to True
    user = User.query.filter_by(email=email).update(dict(approved=True))
    db.session.commit()    
    return render_template('approve.html')

#Account denial route - for use by admin
@main.route('/deny/<email>')
def deny(email):
    #Delete user from database
    user = User.query.filter_by(email=email).delete()
    db.session.commit()
    return render_template('deny.html')

#@auth.before_app_request
#def before_request():
    #if current_user.is_authenticated and not current_user.approved:
        #flash('Your account has not been approved yet')
        #return redirect(url_for('main.index'))

#Data page
@main.route('/data', methods=['GET'])
@login_required
def data():
    form = FilterForm()
    if form.validate_on_submit:
        collection = mongo.db[form.collection.data]
        #Naive solution to possible None form submission: set bounds to (1e-6, 1e6)
        if form.gamma_max.data is None:
            gamma_max = 1e6
        else:
            gamma_max = form.gamma_max.data

        if form.gamma_min.data is None:
            gamma_min = -1e6
        else:
            gamma_min = form.gamma_min.data

        if form.omega_max.data is None:
            omega_max = 1e6
        else:
            omega_max = form.omega_max.data

        if form.omega_min.data is None:
            omega_min = -1e6
        else:
            omega_min = form.omega_min.data

        if form.z_max.data is None:
            z_max = 1e6
        else:
            z_max = form.z_max.data
        
        if form.z_min.data is None:
            z_min = -1e6
        else:
            z_min = form.z_min.data

        if form.lambda_z_max.data is None:
            lambda_z_max = 1e6
        else:
            lambda_z_max = form.lambda_z_max.data
        
        if form.lambda_z_min.data is None:
            lambda_z_min = -1e6
        else:
            lambda_z_min = form.lambda_z_min.data

        #Query the database (instance of Pymongo Cursor class)
        cursor = collection.find(
            {"Parameters.gamma (cs/a)": {$gt: gamma_min, $lt: gamma_max}}, 
            {"Parameters.omega (cs/a)": {$gt: omega_min, $lt: omega_max}}),
            {"Parameters.<z>": {$gt: z_min, $lt: z_max}}, 
            {"Parameters.lambda_z": {$gt: lambda_z_min, $lt: lambda_z_min}})

        #Collect relevant run info from query results
        runs = []
        for run in cursor:
            #Getting upload time of run
            time = run['_id'].generation_time
            #Creating a list of dictionaries with relevant info for run
            params = run['Parameters']
            display_params = []
            for key, value in params.items():
                #Run parameters to be displayed
                display_params.append([key,value])
            temp = {"user": run['Meta']['user'], "keywords": run['Meta']['keywords'], "time": time, "params": display_params}
            runs.append(temp)
    return render_template('data.html', form=form, runs=runs)

#Function for downlaoding run by id
@main.route('/download/<collection>/<id>')
def download_run(collection, id):
    fs = gridfs.GridFSBucket(mongo.db)
    #Get run by id
    run = collection.find_one({"_id": id})
    #Create response from run
    response = make_response(run.read())
    return response   