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
from .forms import SignupForm, FilterForm, LoginForm
from ..email import send_email
from .. import db, mongo
import gridfs
from ..models import User
from flask_paginate import Pagination, get_page_parameter
from io import BytesIO
import base64
from PIL import Image
import datetime
import zipfile

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

#Account approval route  - for use by admin
@main.route('/approve/<email>')
def approve(email):
    #Change "approved" column in database to True
    User.query.filter_by(email=email).update(dict(approved=True))
    db.session.commit()    
    return render_template('approve.html')

#Account denial route - for use by admin
@main.route('/deny/<email>')
def deny(email):
    #Delete user from database
    User.query.filter_by(email=email).delete()
    db.session.commit()
    return render_template('deny.html')

#Data page
@main.route('/data', methods=['GET', 'POST'])
@login_required
def data():
    form = FilterForm()
    if form.validate_on_submit:
        #A collection must always be specified
        collection_name = form.collection.data
        collection = mongo.db[collection_name]
        #Search by ID
        if form.id.data not in ['', None]:
            result = collection.find({"_id": ObjectId(form.id.data)})
            if result is None:
                flash('Run ID returned no results, try again')
                return render_template('data.html', form=form, runs=None, collection_name=collection_name)
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
        #Search with filters
        else:
            #Build dictionary of filters based on user form inputs
            filters = get_filters(form)
            #Query the database
            results = collection.find(filters).sort([['_id', -1]]).limit(10)
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
    return render_template('data.html', form=form, runs=runs, collection_name=collection_name)

@main.route('/img/<collection_name>/<run_id>/<plot_name>')
def get_plot(collection_name, run_id, plot_name):
    collection = mongo.db[collection_name]
    run = collection.find_one({"_id": ObjectId(run_id)})
    plot = run['Plots'][plot_name]
    image = Image.open(BytesIO(base64.decodebytes(plot.encode('utf-8'))))
    return serve_pil_image(image)

#Helper function for get_plot
def serve_pil_image(image):
    img_io = BytesIO()
    image.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

#TODO: Update path to QoIs
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

#Route for downloading run by id
@main.route('/download/<collection_name>/<_id>', methods=['GET'])
def download(collection_name, _id):
    #Intantiate fs objects for downloading from gridfs
    fs = gridfs.GridFSBucket(mongo.db)
    fsf = gridfs.GridFS(mongo.db)
    #Create collection object
    collection = mongo.db[collection_name]
    #Find record
    records_found = collection.find({"_id": ObjectId(_id)})
    #Perform download operations
    for record in records_found:
        #Create timestamp for unique identification
        time = str(datetime.datetime.now()).replace(" ","--")
        #Create directory name for run files
        dir_name = record['Meta']['run_collection_name'].replace("/", "_") + time
        #Create path for directory
        path = "/downloads/" + dir_name
        #Create directory
        os.mkdir(path)

        #Download 'Files'
        for key, val in record['Files'].items():
            if val != 'None':
                filename = mongo.db.fs.files.find_one(val)['filename']
                with open(os.path.join(path, filename),'wb+') as f:
                    fs.download_to_stream(val, f, session=None)     
                record['Files'][key] = str(val)           
        
        #Download 'Gyrokinetics'
        for key, val in record['gyrokinetics'].items():
            if val != 'None':
                file = record['gyrokinetics']
                with open(os.path.join(path, 'gyrokinetics.json'), 'w') as f:
                    json.dump(file, f)

        #Download 'Diagnostics'
        diag_dict = {}
        for key, val in record['Diagnostics'].items():
            if isinstance(val, ObjectId):
                record['Diagnostics'][key] = str(val)
                diag_dict[key] = binary2npArray(fsf.get(val).read())   
        with open(os.path.join(path, str(record['_id']) + '-' + 'diagnostics.pkl'), 'wb') as handle:
            pickle.dump(diag_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        #Download 'Plots'
        plots_path = os.path.join(path, 'plots/')
        os.mkdir(plots_path)
        for key,val in record['Plots'].items():
            with open(os.path.join(plots_path, str(record['_id']) + '_' + key +
                                   record['Meta']['run_suffix'] + '.png'), "wb") as imageFile:
                decoded = base64.decodebytes(val.encode('utf-8'))
                imageFile.write(decoded)
        
        #Download record
        record['_id'] = str(record['_id'])
        f_path = os.path.join(path, 'mgkdb_summary_for_run' + record['Meta']['run_suffix'] + '.json')
        with open(f_path, 'w') as f:
            json.dump(record, f)
        
        #Zip folder
        zip_path = path + ".zip"
        zf = zipfile.ZipFile(zip_path, "w")
        for root, dirs, files in os.walk(path):
            for file in files:
                zf.write(os.path.join(root, file))
        zf.close()

    return send_file(zip_path, mimetype='application/zip', as_attachment=True)

#TODO: Somehow the login_manager isn't being imported from __init__
# @login_manager.unauthorized_handler
# def unauthorized_callback():
#     return redirect(url_for('website.index'))

#Utility function for unpickling numpy arrays (format of stored data)
def binary2npArray(binary):
    return pickle.loads(binary)