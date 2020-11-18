#Base image
FROM python:3.8-slim-buster

#Get required packages
RUN apt-get update && apt-get install -y openssh-server curl nano gcc libjpeg-dev zlib1g-dev

#Environment variables
ENV FLASK_APP mgkdb_web.py
ENV FLASK_DEBUG 1

#Making directory for downloads
RUN mkdir downloads/

#Making directory for app and switching to it
RUN mkdir /app
WORKDIR /app

#Install dependencies (PROD)
#COPY requirements.txt requirements.txt
#RUN pip install -r requirements.txt

#Copy over code (PROD)
#COPY app app
#COPY mgkdb_web.py config.py boot.sh .env ./


