FROM python:3.10.4-alpine3.16

WORKDIR /server
COPY ./requirements.txt ./setup.py ./ 
RUN pip install --no-cache-dir -r requirements.txt
COPY ./ ./ 
WORKDIR /server/src/regps

ENTRYPOINT [ "celery", "-A", "app.tasks", "worker", "--loglevel=debug" ]