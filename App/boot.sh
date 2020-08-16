#!/bin/bash

#Activate virtual environment
source venv/bin/activate

#Connect to MySQL database (retry until success)
while true; do
    #For first time deploying
    python -m flask db init
    #python -m flask db upgrade
    #Only breaks once exit status of deploy command is 0
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo DB failed, retrying...
    #Try once every second
    sleep 5
done

#Run web server
exec gunicorn -w 2 -b 0.0.0.0:5000 --access-logfile - --error-logfile - mgkdb_web:app