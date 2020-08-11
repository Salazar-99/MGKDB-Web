#Base image
FROM python:3.8-slim-buster

#Get SSH
RUN apt-get update && apt-get install -y openssh-server

#Environment variables
ENV FLASK_APP mgkdb_web.py
ENV FLASK_DEBUG 1

#Making directory for app and switching to it
RUN mkdir /app
WORKDIR /app

#Install dependencies
COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt

#Copy over code
COPY app app
COPY mgkdb_web.py config.py boot.sh .env ./

#Start app
EXPOSE 5000
ENTRYPOINT [ "./boot.sh" ]