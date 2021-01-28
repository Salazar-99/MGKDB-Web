import os
from flask import Flask, Response, render_template, url_for, session, redirect, flash, request, make_response, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import pickle
import json
from io import BytesIO
from zipfile import ZipFile
from . import main
from .forms import SignupForm, FilterForm, LoginForm, PageForm
from ..email import send_email
from .. import db, mongo
import gridfs
from ..models import User, Task, Notification
from flask_paginate import Pagination, get_page_parameter
from io import BytesIO
import base64
from PIL import Image
import datetime
import zipfile
from time import sleep

#Home page
@main.route('/')
def index():
    return render_template('index.html', logged_in=False)

@main.route('/getting-started')
def getting_started():
    return render_template('getting-started.html')

@main.route('/about')
def about():
    return render_template('about.html')

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

#TODO: Add security measures to approve/deny routes
#Account approval route  - for use by admin
@main.route('/approve/<email>')
def approve(email):
    #Change "approved" column in database to True
    User.query.filter_by(email=email).update(dict(approved=True))
    db.session.commit()
    send_email(email, 'Account Approved', 'mail/approve')
    return render_template('approve.html')

#Account denial route - for use by admin
@main.route('/deny/<email>')
def deny(email):
    #Delete user from database
    User.query.filter_by(email=email).delete()
    db.session.commit()
    return render_template('deny.html')

@main.route('/data_form', methods=['GET','POST'])
@login_required
def data_form():
    form = FilterForm()
    if form.validate_on_submit():
        collection_name = form.collection.data
        #Single run
        if form.id.data not in ['None', '']:
            return redirect(url_for('main.data_single_run', collection_name=collection_name, single_run_id=form.id.data))
        #Multiple runs
        else:
            #Get filters dict and convert to string
            filters = str(get_filters(form))
            return redirect(url_for('main.data', filters=filters, collection_name=collection_name, page_num=1))
    return render_template('data_form.html', form=form)

#Data page for a single run, search by id
@main.route('/data_single_run/<collection_name>/<single_run_id>', methods=['GET'])
@login_required
def data_single_run(collection_name, single_run_id):
    collection = mongo.db[collection_name]
    result = collection.find({"_id": ObjectId(single_run_id)})
    if result is None:
        flash('Run ID returned no results, try again')
        return redirect(url_for('main.data_form'))
    else:
        runs = []
        #Should just be one result, keeping loop for consistency in rendering
        for run in result:
            #Getting upload time of run
            time = run['_id'].generation_time.date()
            #Collecting params
            params = run['gyrokinetics']['code']['parameters']
            display_params = []
            for key, value in params.items():
                display_params.append([key,value])
            #Collecting plots
            plots = run['Plots']
            plot_names = []
            for name in plots:
                plot_names.append(name)
            temp = {"id": run['_id'], "user": run['Meta']['user'], "keywords": run['Meta']['keywords'], 
                    "time": time, "params": display_params, "plot_names": plot_names}
            runs.append(temp)
    return render_template('data_single_run.html', runs=runs)

#Data page for multiple runs, search by filters
@main.route('/data/<filters>/<collection_name>/<page_num>', methods=['GET', 'POST'])
@login_required
def data(filters, collection_name, page_num):
    #Search for specific page
    form = PageForm()
    if form.validate_on_submit():
        return redirect(url_for('main.data', filters=filters, collection_name=collection_name, page_num=form.page.data))
    #Number of results per page
    PAGE_LIMIT = 10
    #URL arguments passed as strings, need to convert to int for query
    page_num = int(page_num)
    collection = mongo.db[collection_name]
    #Get filters dict from filters string
    filters = eval(filters)
    #Query the database with pagination, limit hardcoded to 10
    max_pages = collection.count(filters) // PAGE_LIMIT
    results = collection.find(filters).sort([['_id', -1]]).skip((page_num-1)*PAGE_LIMIT).limit(PAGE_LIMIT)
    #Collect data for all runs in result
    runs = []
    for run in results:
        #Getting upload time of run
        time = run['_id'].generation_time.date()
        #Collecting params
        params = run['gyrokinetics']['code']['parameters']
        display_params = []
        for key, value in params.items():
            display_params.append([key,value])
        #Collecting plot names
        plots = run['Plots']
        plot_names = []
        for name in plots:
            plot_names.append(name)
        #Dictionary for access in template
        temp = {"id": run['_id'], "user": run['Meta']['user'], "keywords": run['Meta']['keywords'], 
                "time": time, "params": display_params, "plot_names": plot_names}
        runs.append(temp)
    return render_template('data.html', form=form, runs=runs, filters=filters, collection_name=collection_name, page_num=page_num, max_pages=max_pages)

#TODO: Fix "Cannot identify image file", might not be an error on my end
@main.route('/img/<collection_name>/<run_id>/<plot_name>')
def get_plot(collection_name, run_id, plot_name):
    collection = mongo.db[collection_name]
    run = collection.find_one({"_id": ObjectId(run_id)})
    plot = run['Plots'][plot_name]
    #Error here
    image = Image.open(BytesIO(base64.decodebytes(plot.encode('utf-8'))))
    return serve_pil_image(image)

#Helper function for get_plot
def serve_pil_image(image):
    img_io = BytesIO()
    image.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

#Function for parsing filter values
def get_filters(form):
    filters = {}
    for field in form:
        #Ignore empty fields
        if field.data not in [None, ""]:
            #Check if field is a max or min filter (ignores collection, submit, token)
            if field.label.text.endswith("max"):
                filters.update({field.id: {"$lt": float(field.data)}})
            elif field.label.text.endswith("min"):
                #Check if a filter already exists to prevent overwriting
                try:
                    filters[field.id].update({"$gt": float(field.data)})
                except KeyError:
                    filters.update({field.id: {"$gt": float(field.data)}})
    return filters

#Route for dynamic notifications
@main.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])

#Route for downloading run by id
@main.route('/download_one/<collection_name>/<_id>', methods=['GET'])
@login_required
def download_one(collection_name, _id):
    if current_user.get_task_in_progress('download_one') or current_user.get_task_in_progress('download_all'):
        flash('A download task is currently in progress')
    else:
        task = current_user.launch_task(name='download_one', description='Downloading run...')
        db.session.commit()
        path = set_target_path(task)
        wait_for_download(path)
        return send_file(path, mimetype='application/zip', as_attachment=True)
    return redirect(url_for('main.data', filters=filters, collection_name=collection_name, page_num=1))

#Route for downloading all results of a search
@main.route('/download_all/<collection_name>/<filters>', methods=['GET'])
@login_required
def download_all(collection_name, filters):
    if current_user.get_task_in_progress('download_one') or current_user.get_task_in_progress('download_all'):
        flash('A download task is currently in progress')
    else:
        task = current_user.launch_task(name='download_all', description='Downloading runs...')
        db.session.commit()
        path = set_target_path(task)
        wait_for_download(path)
        return send_file(path, mimetype='application/zip', as_attachment=True)
    return redirect(url_for('main.data', filters=filters, collection_name=collection_name, page_num=1))

def set_target_path(task):
    path = '/downloads/' + str(task.id)
    return path

def wait_for_download(path):
    #Wait for file to appear
    time = 0
    while not os.path.exists(path):
        sleep(1)
        time += 1
        print(f"Waiting for file to appear...({time} seconds)")
    #Check size of file until it stops changing (download is complete)
    size = os.path.getsize(path)
    sleep(0.25)
    new_size = os.path.getsize(path)
    while size != new_size:
        size = os.path.getsize(path)
        sleep(0.25)
        new_size = os.path.getsize(path)

#Utility function for unpickling numpy arrays (format of stored data)
def binary2npArray(binary):
    return pickle.loads(binary)