from app import create_app, db, mongo
from app.models import Task
from rq import get_current_job
import os
import shutil

#Get current app context for Redis to access
app = create_app()
app.app_context().push()

#TODO Refactor download logic to match routes in views.py

#Download all Redis Task
def download_all(user_id, collection_name, filters):
    try:
        #Set path for downloading the results and get job object
        job = get_current_job()

        #Find runs matching filters
        collection = mongo.db[collection_name]
        results = collection.find(filters)

        #Get number of results
        N = results.count()

        #Paths list to hold the paths of each zipped result
        paths = []

        #Main loop, downloads each result and appends its path to paths
        set_task_progress(0)
        i = 0
        for run in results:
            path = download_one(collection_name, run['_id'])
            paths.append(path)
            i += 1
            set_task_progress(100*(i//N))

        #Make target_path directory and move all zipped run directories into it
        if not os.path.isdir(target_path):
            os.mkdir(target_path)
        for file in paths:
            shutil.move(file, target_path)

        #Zip target_path directory
        zip_path = target_path + ".zip"
        zf = zipfile.ZipFile(zip_path, "w")
        for root, dirs, files in os.walk(target_path):
            for file in files:
                zf.write(os.path.join(root, file))
        zf.close()

    except:
        app.logger.error('Redis task error', exc_info=sys.exc_info())

#Download one Redis Task
def download_one(collection_name, _id):
    try: 
        zip_path = download(collection_name, _id)
    except:
        app.logger.error('Redis task error', exc_info=sys.exc_info())

#Download one run function for use in tasks
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
            #Save zip path to DB
            zip_path = path + ".zip"
            save_path_to_db(job, zip_path)
            
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
            zf = zipfile.ZipFile(zip_path, "w")
            for root, dirs, files in os.walk(path):
                for file in files:
                    zf.write(os.path.join(root, file))
            zf.close()

        return zip_path

def set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user_id.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def set_target_path(job):
    path = '/downloads/' + str(job.get_id)
    return path