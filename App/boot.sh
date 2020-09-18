#!/bin/bash

#Connect to MySQL database (retry until success)
while true; do
    #For first time deploying
    #python -m flask db init
    python -m flask db upgrade
    #Only breaks once exit status of above command is 0
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo DB failed, retrying...
    #Try once every 10 seconds
    sleep 10
done

#Run web server (--reload for DEV only)
exec gunicorn -w 2 -b 0.0.0.0:5000 --reload --access-logfile - --error-logfile - mgkdb_web:app