# import asyncio
# import falcon.asgi
import base64
import falcon
from falcon import media
from falcon.http_status import HTTPStatus
import gunicorn
import json
import os
from swagger_ui import api_doc
from app.tasks import check_login, check_upload, upload, verify
# import uvicorn

class LoginTask(object):

    def on_post(self, req, resp):
        print("LoginTask.on_post")
        try:
            raw_json = req.stream.read()
            data = json.loads(raw_json)
            print(f"LoginTask.on_post: sending data {data}")
            result = verify(data['aid'], data['said'], data['vlei'])
            print(f"LoginTask.on_post: received data {result}")
            resp.status = falcon.code_to_http_status(result.status_code)
            resp.text = result.text
            resp.content_type = result.headers['Content-Type']
        except Exception as e:
            print(f"LoginTask.on_post: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
    def on_get(self, req, resp, aid):
        print("LoginTask.on_get")
        try:
            # raw_json = req.stream.read()
            # data = json.loads(raw_json)
            print(f"LoginTask.on_get: sending aid {aid}")
            result = check_login(aid)
            print(f"LoginTask.on_get: received data {result}")
            resp.status = falcon.code_to_http_status(result.status_code)
            resp.text = result.text
            resp.content_type = result.headers['Content-Type']
        except Exception as e:
            print(f"LoginTask.on_get: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
class UploadTask(object):
    
    def on_post(self, req, resp):
        print("UploadTask.on_post")
        try:
            raw_json = req.stream.read()
            data = json.loads(raw_json)
            print(f"UploadTask.on_post: sending data {data}")
            result = upload(data['aid'], data['said'], data['vlei'])
            print(f"UploadTask.on_post: received data {result}")
            resp.status = falcon.code_to_http_status(result.status_code)
            resp.text = result.text
            resp.content_type = result.headers['Content-Type']
        except Exception as e:
            print(f"UploadTask.on_post: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
    def on_get(self, req, resp, aid, said):
        print("UploadTask.on_get")
        try:
            # raw_json = req.stream.read()
            # data = json.loads(raw_json)
            print(f"UploadTask.on_get: sending aid {aid} for said {said}")
            result = check_upload(aid, said)
            print(f"UploadTask.on_get: received data {result}")
            resp.status = falcon.code_to_http_status(result.status_code)
            resp.text = result.text
            resp.content_type = result.headers['Content-Type']
        except Exception as e:
            print(f"UploadTask.on_get: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500

class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, body='\n')

class PingResource:
   def on_get(self, req, resp):
      """Handles GET requests"""
      resp.status = falcon.HTTP_200
      resp.content_type = falcon.MEDIA_TEXT
      resp.text = (
         'Pong'
      )

def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(description=f"required field '{name}' missing from request")

    return param

def swagger_ui(app):
    vlei_contents = None
    with open('app/data/credential.cesr', 'r') as cfile:
        vlei_contents = cfile.read()

    report_zip = None
    with open('app/data/report.zip', 'rb') as rfile:        
        report_zip = rfile

    config = {"openapi":"3.0.1",
            "info":{"title":"Regulator portal service api","description":"Regulator web portal service api","version":"1.0.0"},
            "servers":[{"url":"http://127.0.0.1:8000","description":"local server"}],
            "tags":[{"name":"default","description":"default tag"}],
            "paths":{"/ping":{"get":{"tags":["default"],"summary":"output pong.","responses":{"200":{"description":"OK","content":{"application/text":{"schema":{"type":"object","example":"Pong"}}}}}}},
                    "/login":{"post":{"tags":["default"],
                                        "summary":"Given an AID and vLEI, returns information about the login",
                                        "requestBody":{"required":"true","content":{"application/json":{"schema":{"type":"object","properties":{
                                            "aid":{"type":"string","example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},
                                            "said":{"type":"string","example":"EAPHGLJL1s6N4w1Hje5po6JPHu47R9-UoJqLweAci2LV"},
                                            "vlei":{"type":"string","example":f"{vlei_contents}"}
                                            }}}}},
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{"status": "200 OK", "message": "AID and vLEI valid login"}}}}}}
                                        }},
                    "/checklogin/{aid}":{"get":{"tags":["default"],
                                        "summary":"Given an AID returns information about the login",
                                        "parameters":[{"in":"path","name":"aid","required":"true","schema":{"type":"string","minimum":1,"example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},"description":"The AID"}],
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{"status": "200 OK", "message": "AID logged in"}}}}}}
                                        }},
                    "/upload/{aid}/{said}":{"post":{"tags":["default"],
                                        "summary":"Given an report, returns information about the upload",
                                        "requestBody":{"required":"true","content":{"multipart/form-data":{"schema":{"type":"object","properties":{
                                            "aid":{"type":"string","example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},
                                            "said":{"type":"string","example":"EAPHGLJL1s6N4w1Hje5po6JPHu47R9-UoJqLweAci2LV"},
                                            "upload":{"type":"string","format":"binary","example":f"{report_zip}"}
                                            }}}}},
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{"status": "200 OK", "message": "AID and vLEI valid login"}}}}}}
                                        }},
                    "/checkupload/{aid}/{said}":{"get":{"tags":["default"],
                                        "summary":"Given an AID returns information about the upload status",
                                        "parameters":[{"in":"path","name":"aid","required":"true","schema":{"type":"string","minimum":1,"example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},"description":"The AID"},
                                                      {"in":"path","name":"said","required":"true","schema":{"type":"string","minimum":1,"example":"EAPHGLJL1s6N4w1Hje5po6JPHu47R9-UoJqLweAci2LV"},"description":"The SAID of the upload"}],
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{"status": "200 OK", "message": "AID logged in"}}}}}}
                                        }}
                    }}

    doc = api_doc(app, config=config, url_prefix='/api/doc', title='API doc', editor=True)
    return doc

def falcon_app():
    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['content-type', 'signature', 'signature-input'])
        )
# if os.getenv("KERI_AGENT_CORS", "false").lower() in ("true", "1"):
    app.add_middleware(middleware=HandleCORS())
    print("CORS  enabled")
    # app.add_middleware(authing.SignatureValidationComponent(agency=agency, authn=authn, allowed=["/agent"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    # app = falcon.asgi.App()
    ping = PingResource()
    app.add_route('/ping', ping)
    app.add_route('/login', LoginTask())
    app.add_route("/checklogin/{aid}", LoginTask())
    app.add_route('/upload', UploadTask())
    app.add_route("/checkupload/{aid}", UploadTask())
    
    return app

# async def appl(scope, receive, send):
#     assert scope['type'] == 'http'

#     await send({
#         'type': 'http.response.start',
#         'status': 200,
#         'headers': [
#             [b'content-type', b'text/plain'],
#         ],
#     })
#     await send({
#         'type': 'http.response.body',
#         'body': b'Hello, world!',
#     })
    
def main():
    print("Starting RegPS...")
    app = falcon_app()
    api_doc=swagger_ui(app)

    return app
    
if __name__ == '__main__':
    main()