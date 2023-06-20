# regps/app/tasks.py

import celery
import falcon
import os
import requests
from time import sleep

dbrok = "redis://redis:6379/0"
dback = "redis://redis:6379/0"

CELERY_BROKER = os.environ.get('CELERY_BROKER')
if CELERY_BROKER is None:
    print(f"CELERY_BROKER is not set. Using default {dbrok}")
    CELERY_BROKER = dbrok
CELERY_BACKEND = os.environ.get('CELERY_BACKEND')
if CELERY_BACKEND is None:
    print(f"CELERY_BACKEND is not set. Using default {dback}")
    CELERY_BACKEND = dback
    
app = celery.Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)

aurl = "http://localhost:7676/authorizations/"
purl = "http://localhost:7676/presentations/"
rurl = "http://localhost:7676/reports/"

@app.task
def check_login(aid) -> falcon.Response:
    print("checking login: aid {}".format(aid))
    gres = requests.get(aurl+f"{aid}", headers={"Content-Type": "application/json"})
    print("login status: {}".format(gres))
    return gres

@app.task
def verify(aid,said,vlei) -> falcon.Response:
    # first check to see if we're already logged in
    gres = check_login(aid)
    print("Login check {} {}".format(gres.status_code,gres.text))
    if str(gres.status_code) == str(falcon.http_status_to_code(falcon.HTTP_ACCEPTED)):
        print("already logged in")
        return gres
    else:
        print("putting to {}".format(purl+f"{said}"))
        pres = requests.put(purl+f"{said}", headers={"Content-Type": "application/json+cesr"}, data=vlei)
        print("put response {}".format(pres.text))
        if pres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            gres = None
            while(gres == None or gres.status_code == falcon.http_status_to_code(falcon.HTTP_404)):
                gres = check_login(aid)
                print("polling result {}".format(gres.text))
                sleep (1)
            return gres
        else:
            return pres
        
@app.task
def check_upload(aid, dig) -> falcon.Response:
    print("checking upload: aid {} and said {}".format(aid,dig))
    gres = requests.get(rurl+f"{aid}/{dig}", headers={"Content-Type": "application/json"})
    print("upload status: {}".format(gres))
    return gres

@app.task
def upload(aid,dig,report) -> falcon.Response:
    # first check to see if we've already uploaded
    gres = check_upload(aid,dig)
    if gres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
        print("already uploaded")
        return gres
    else:
        print("putting to {}".format(purl+f"{dig}"))
        pres = requests.post(rurl+f"{aid}/{dig}", headers={"Content-Type": "multipart/form-data"}, data=report)
        print("put response {}".format(pres.text))
        if pres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            gres = None
            while(gres == None or gres.status_code == falcon.http_status_to_code(falcon.HTTP_404)):
                gres = check_upload(aid,dig)
                print("polling result {}".format(gres.text))
                sleep (1)
            return gres
        else:
            return pres