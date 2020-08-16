import os
from flask import Flask, Response, render_template, url_for, session, redirect, flash, request, make_response, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import pickle
from io import BytesIO
from zipfile import ZipFile
from . import main
from .forms import SignupForm, FilterForm, LoginForm
from ..email import send_email
from .. import db, mongo
import gridfs
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
    fs = gridfs.GridFSBucket(mongo.db)
    if form.validate_on_submit:
        collection_name = form.collection.data
        collection = mongo.db[collection_name]
        #Search by ID
        if form.id.data not in ['', None]:
            result = collection.find({"_id": form.id.data})
            if result is None:
                flash('Run ID returned no results, try again')
                return render_template('data.html', form=form, runs=runs, collection_name=collection_name)
            else:
                run = []
                #Getting upload time of run
                time = run['_id'].generation_time.date()
                #Creating a list of dictionaries with relevant info for run
                params = run['Parameters']
                display_params = []
                for key, value in params.items():
                    #Run parameters to be displayed
                    display_params.append([key,value])
                size = fs.chunks.find({"id": id}).count() * 255 / 1024
                run = {"id": run['_id'], "user": run['Meta']['user'], "keywords": run['Meta']['keywords'], 
                        "time": time, "params": display_params, "size": size}
                runs.append(run)
        #Search with filters
        else:
            #Build dictionary of filters based on user form inputs
            filters = get_filters(form)
            #Query the database (newest to oldest)
            cursor = collection.find(filters).sort([['_id', -1]])
            #Collect relevant run info from query results
            runs = []
            for run in cursor:
                #Getting upload time of run
                time = run['_id'].generation_time.date()
                size = fs.chunks.find({"id": run['_id']}).count() * 255 / 1024
                #Creating a list of dictionaries with relevant info for run
                params = run['Parameters']
                display_params = []
                for key, value in params.items():
                    #Run parameters to be displayed
                    display_params.append([key,value])
                temp = {"id": run['_id'], "user": run['Meta']['user'], "keywords": run['Meta']['keywords'], 
                        "time": time, "params": display_params, "size": size}
                runs.append(temp)
    return render_template('data.html', form=form, runs=runs, collection_name=collection_name)

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
@main.route('/download/<collection_name>/<id>', methods=['GET'])
def download(collection_name, id):
    #Instantiate fs object
    fs = gridfs.GridFSBucket(mongo.db)
    #Set collection
    collection = mongo.db[collection_name]
    #Find metadata for run
    record = collection.find_one({"_id": id})
    #Save metadata as summary
    summary = json.dumps(record)
    #Save 'Files'
    for key, val in record['Files'].items():
        if val != "None":
            filename = db.fs.files.find_one(val)['filename']
            with open('filename','wb+') as f:
                fs.download_to_stream(val, f, session=None)
            record['Files'][key] = str(val)
    #Save 'Diagnostics'
    diagnostics = {}
    for key, val in record['Diagnostics'].items():
        if isinstance(val, ObjectId):
            record['Diagnostics'][key] = str(val)
            diagnostics[key] = binary_to_numpy(fs.get(val).read())
    #Save 'Plots'
    for key,val in record['Plots'].items():
            with open(os.path.join(path, str(record['_id']) + '_' +key+
                                   record['Meta']['run_suffix']+'.png'), "wb") as imageFile:
                decoded = base64.decodebytes(val.encode('utf-8'))
                imageFile.write(decoded)
    #Combine all data into zip folder
    #memory_file = BytesIO()
    #for file in [records, diagnostics]:

    #return send_file(data, attachment_filename=f'{id}.zip', as_attachment=True)

#Utility function for unpickling numpy arrays (format of stored data)
def binary_to_numpy(x):
    return pickle.loads(x)