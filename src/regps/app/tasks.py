# regps/app/tasks.py

import celery
import falcon
import json
import os
import requests
from time import sleep

# dbrok = "redis://127.0.0.1:6379/0"
# dback = "redis://127.0.0.1:6379/0"

# CELERY_BROKER = os.environ.get('CELERY_BROKER')
# if CELERY_BROKER is None:
#     print(f"CELERY_BROKER is not set. Using default {dbrok}")
#     CELERY_BROKER = dbrok
# CELERY_BACKEND = os.environ.get('CELERY_BACKEND')
# if CELERY_BACKEND is None:
#     print(f"CELERY_BACKEND is not set. Using default {dback}")
#     CELERY_BACKEND = dback
    
# app = celery.Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)

aurl = "http://localhost:7676/authorizations/"
purl = "http://localhost:7676/presentations/"
repurl = "http://localhost:7676/reports/"
requrl = "http://localhost:7676/request/verify/"

# VERIFIER_AUTHORIZATIONS = os.environ.get('VERIFIER_AUTHORIZATIONS')
# if VERIFIER_AUTHORIZATIONS is None:
#         print(f"VERIFIER_AUTHORIZATIONS is not set. Using default {aurl}")
# else:
#         print(f"VERIFIER_AUTHORIZATIONS is set. Using {VERIFIER_AUTHORIZATIONS}")
#         aurl = VERIFIER_AUTHORIZATIONS
        
# VERIFIER_PRESENTATIONS = os.environ.get('VERIFIER_PRESENTATIONS')
# if VERIFIER_PRESENTATIONS is None:
#         print(f"VERIFIER_PRESENTATIONS is not set. Using default {purl}")
# else:
#         print(f"VERIFIER_PRESENTATIONS is set. Using {VERIFIER_PRESENTATIONS}")
#         purl = VERIFIER_PRESENTATIONS

# VERIFIER_REPORTS = os.environ.get('VERIFIER_REPORTS')
# if VERIFIER_REPORTS is None:
#         print(f"VERIFIER_REPORTS is not set. Using default {repurl}")
# else:
#         print(f"VERIFIER_REPORTS is set. Using {VERIFIER_REPORTS}")
#         repurl = VERIFIER_REPORTS
        
# VERIFIER_REQUESTS = os.environ.get('VERIFIER_REQUESTS')
# if VERIFIER_REQUESTS is None:
#         print(f"VERIFIER_REQUESTS is not set. Using default {requrl}")
# else:
#         print(f"VERIFIER_REQUESTS is set. Using {VERIFIER_REQUESTS}")
#         repurl = VERIFIER_REQUESTS

# @app.task
def check_login(aid):
    print("checking login: aid {}".format(aid))
    gres = requests.get(aurl+f"{aid}", headers={"Content-Type": "application/json"})
    print("login status: {}".format(gres))
    return serResp(gres)

# @app.task
def verify_rep(aid,said,vlei):
    # first check to see if we're already logged in
    print("Login verification started {} {}....".format(aid,said,vlei[:50]))
    gres = check_login(aid)
    print("Login check {} {}....".format(gres["status_code"],gres["text"][:50]))
    if str(gres["status_code"]) == str(falcon.http_status_to_code(falcon.HTTP_OK)):
        print("already logged in")
        return gres
    else:
        print("putting to {}".format(purl+f"{said}"))
        pres = requests.put(purl+f"{said}", headers={"Content-Type": "application/json+cesr"}, data=vlei)
        print("put response {}".format(pres.text))
        if pres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            gres = None
            while(gres == None or gres["status_code"] == falcon.http_status_to_code(falcon.HTTP_404)):
                gres = check_login(aid)
                print("polling result {}".format(gres["text"]))
                sleep (1)
            return serResp(gres)
        else:
            return serResp(pres)
        
# @app.task
def verify_req(req):
    print("Request verification started {}....".format(req))
    print("putting to {}".format(requrl+f"{req}"))
    print(f"verify_req headers {req.headers}")
    pres = requests.post(requrl+"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei")
    print("put response {}".format(pres.text))
    return serResp(pres)
        
# @app.task
def check_upload(aid, dig):
    print("checking upload: aid {} and dig {}".format(aid,dig))
    gres = requests.get(repurl+f"{aid}/{dig}", headers={"Content-Type": "application/json"})
    print("upload status: {}".format(gres))
    return serResp(gres)

# @app.task
def upload(aid,dig,contype,report):
    # first check to see if we've already uploaded
    gres = check_upload(aid,dig)
    if gres["status_code"] == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
        print("already uploaded")
        return gres
    else:
        print("posting to {}".format(repurl+f"{dig}"))
        pres = requests.post(repurl+f"{aid}/{dig}", headers={"Content-Type": contype}, data=report)
        print("post response {}".format(pres.text))
        if pres.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            gres = None
            while(gres == None or gres["status_code"] == falcon.http_status_to_code(falcon.HTTP_404)):
                gres = check_upload(aid,dig)
                print("polling result {}".format(gres["text"]))
                sleep (1)
            return gres
        else:
            return serResp(pres)
        
def serResp(resp):
    sResp = {"status_code": resp.status_code, "text": resp.text, "headers":{"Content-Type":resp.headers['Content-Type']}}
    print("serializing response {}".format(sResp))
    return sResp