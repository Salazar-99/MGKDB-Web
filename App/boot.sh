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
    sleep 1
done

#TODO: Figure out identity file to make this work
#Port forwarding for accessing MGKDB on Cori via localhost
ssh -i .ssh/nersc -f gsalazar@cori.nersc.gov -L 2222:mongodb03.nersc.gov:27017 -N

#Run web server
exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - mgkdb_web:app