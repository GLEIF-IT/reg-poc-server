# base image
FROM python:3.11-alpine

RUN apk update
RUN apk add bash
RUN apk add git

# set working directory
WORKDIR /usr/src/app/regps

# add app
COPY ./src /usr/src/app/regps/src
COPY ./setup.py /usr/src/app/regps/setup.py
COPY ./requirements.txt /usr/src/app/regps/requirements.txt

# install requirements
RUN pip install --no-cache-dir -r requirements.txt