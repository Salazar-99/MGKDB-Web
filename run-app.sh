#!/bin/bash

#This script automates the steps for starting the MGKDGB Web flask app

#Start virtual environment
source mgkdb-web-venv/bin/activate

#Setup environment variables
export FLASK_APP=mgkdb_web.py
export FLASK_DEBUG=1

#Start flask app
flask run