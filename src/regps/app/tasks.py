# regps/app/tasks.py

import celery
import falcon
import os
import requests
from time import sleep
from celery.utils.log import get_task_logger
    
logger = get_task_logger(__name__)

# dbrok = "redis://127.0.0.1:6379/0"
# dback = "redis://127.0.0.1:6379/0"

# CELERY_BROKER = os.environ.get('CELERY_BROKER')
# if CELERY_BROKER is None:
#     logger.debug(f"CELERY_BROKER is not set. Using default {dbrok}")
#     CELERY_BROKER = dbrok
# CELERY_BACKEND = os.environ.get('CELERY_BACKEND')
# if CELERY_BACKEND is None:
#     logger.debug(f"CELERY_BACKEND is not set. Using default {dback}")
#     CELERY_BACKEND = dback
    
# app = celery.Celery('tasks', broker=CELERY_BROKER, backend=CELERY_BACKEND)

auths_url = "http://127.0.0.1:7676/authorizations/"
presentations_url = "http://127.0.0.1:7676/presentations/"
reports_url = "http://127.0.0.1:7676/reports/"
request_url = "http://localhost:7676/request/verify/"

# VERIFIER_AUTHORIZATIONS = os.environ.get('VERIFIER_AUTHORIZATIONS')
# if VERIFIER_AUTHORIZATIONS is None:
#         logger.debug(f"VERIFIER_AUTHORIZATIONS is not set. Using default {auths_url}")
# else:
#         logger.debug(f"VERIFIER_AUTHORIZATIONS is set. Using {VERIFIER_AUTHORIZATIONS}")
#         auths_url = VERIFIER_AUTHORIZATIONS
        
# VERIFIER_PRESENTATIONS = os.environ.get('VERIFIER_PRESENTATIONS')
# if VERIFIER_PRESENTATIONS is None:
#         logger.debug(f"VERIFIER_PRESENTATIONS is not set. Using default {presentations_url}")
# else:
#         logger.debug(f"VERIFIER_PRESENTATIONS is set. Using {VERIFIER_PRESENTATIONS}")
#         presentations_url = VERIFIER_PRESENTATIONS

# VERIFIER_REPORTS = os.environ.get('VERIFIER_REPORTS')
# if VERIFIER_REPORTS is None:
#         logger.debug(f"VERIFIER_REPORTS is not set. Using default {reports_url}")
# else:
#         logger.debug(f"VERIFIER_REPORTS is set. Using {VERIFIER_REPORTS}")
#         reports_url = VERIFIER_REPORTS

# @app.task
def check_login(aid: str) -> dict:
    return serialize(_login(aid))

def _login(aid: str) -> falcon.Response:
    logger.debug(f"checking login: {aid}")

    gres = requests.get(f"{auths_url}{aid}", headers={"Content-Type": "application/json"})
    logger.debug(f"login status: {gres}")
    return gres

# @app.task
def verify_vlei(aid: str, said: str, vlei: str) -> dict:
    # first check to see if we're already logged in
    logger.debug(f"Login verification started {aid} {said} {vlei[:50]}")

    login_response = _login(aid)
    logger.debug(f"Login check {login_response.status_code} {login_response.text[:50]}")

    if str(login_response.status_code) == str(falcon.http_status_to_code(falcon.HTTP_OK)):
        logger.debug("already logged in")
        return serialize(login_response)
    else:
        logger.debug(f"putting to {presentations_url} {said}")
        presentation_response = requests.put(f"{presentations_url}{said}", headers={"Content-Type": "application/json+cesr"}, data=vlei)
        logger.debug(f"put response {presentation_response.text}")

        if presentation_response.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            login_response = None
            while(login_response == None or login_response.status_code == falcon.http_status_to_code(falcon.HTTP_404)):
                login_response = _login(aid)
                logger.debug(f"polling result {login_response}")
                sleep (1)
            return serialize(login_response)
        else:
            return serialize(presentation_response)
        
# @app.task
def verify_req(aid,cig,ser):
    print("Request verification started aid = {}, cig = {}, ser = {}....".format(aid,cig,ser))
    print("posting to {}".format(request_url+f"{aid}"))
    print(f"verify_req headers {aid}")
    pres = requests.post(request_url+aid, params={"sig": cig,"data": ser})
    print("post response {}".format(pres.text))
    return serialize(pres)
        
# @app.task
def check_upload(aid: str, dig: str) -> dict:
    return serialize(_upload(aid, dig))

def _upload(aid: str, dig: str) -> falcon.Response:
    logger.debug(f"checking upload: aid {aid} and dig {dig}")
    reports_response = requests.get(f"{reports_url}{aid}/{dig}", headers={"Content-Type": "application/json"})
    logger.debug(f"upload status: {reports_response}")
    return reports_response

# @app.task
def upload(aid: str, dig: str, contype: str, report) -> dict:
    logger.debug(f"report type {type(report)}")
    # first check to see if we've already uploaded
    upload_response = _upload(aid, dig)
    if upload_response.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
        logger.debug("already uploaded")
        return serialize(upload_response)
    else:
        logger.debug(f"posting to {reports_url} {dig}")
        presentation_response = requests.post(f"{reports_url}{aid}/{dig}", headers={"Content-Type": contype}, data=report)
        logger.debug(f"post response {presentation_response.text}")

        if presentation_response.status_code == falcon.http_status_to_code(falcon.HTTP_ACCEPTED):
            upload_response = None
            while(upload_response == None or upload_response.status_code == falcon.http_status_to_code(falcon.HTTP_404)):
                upload_response = _upload(aid,dig)
                logger.debug(f"polling result {upload_response.text}")
                sleep (1)
            return serialize(upload_response)
        else:
            return serialize(presentation_response)
        
def serialize(response: falcon.Response) -> dict:
    return {"status_code": response.status_code, "text": response.text, "headers":{"Content-Type": response.headers['Content-Type']}}