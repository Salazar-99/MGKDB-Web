#!/bin/bash

#This is a convenience script for starting up all of the process needed to develop MGKDB Web

#Start MySQL
echo "Starting MySQL..."
sudo service mysql start 
if [[ "$(systemctl is-active mysql)" = "active" ]]
then 
    echo "MySQL is running"
else
    echo "MySQL failed to start!"
fi 

#Start MongoDB
echo "Starting MongoDB..."
sudo service mongod start 
if [[ "$(systemctl is-active mongod)" = "active" ]]
then 
    echo "MongoDB is running"
else
    echo "MongoDB failed to start!"
fi 

#Start flask app in new terminal and suppress output
gnome-terminal -e ./run-app.sh &>/dev/null

#Open up code editor
code /home/gerardo/Desktop/Projects/MGKDB-Web 

#Open up localhost in browser and suppress output
chromium-browser http://127.0.0.1:5000/ &>/dev/null
