from app.tasks import check_login, check_upload, upload, verify_vlei, verify_req
# from celery.result import AsyncResult
import falcon
from falcon import media
from falcon.http_status import HTTPStatus
import json
from keri import kering
from keri.end import ending
import os
from swagger_ui import api_doc
import time

uploadStatus = {}

class AuthSigs(object):

    DefaultFields = ["Signify-Resource",
                     "@method",
                     "@path",
                     "Signify-Timestamp"]

    def __init__(self):
        """ Create Agent Authenticator for verifying requests and signing responses
        Parameters:
            agency(Agency): habitat of Agent for signing responses
        Returns:
              Authenicator:  the configured habery
        """
        # self.agency = agency

    def process_request(self, req, resp):
        print(f"Processing header verification request {req}")
        result = self.verify(req)
        print(f"Header verification request {result}")

    def on_post(self, req, resp):
        print(f"Processing header verification request {req}")
        result = self.verify(req)
        resp.status = falcon.code_to_http_status(result["status_code"])
        resp.text = result["text"]
        resp.content_type = result["headers"]['Content-Type']
        print(f"Header verification request {resp}")

    @staticmethod
    def resource(req):
        headers = req.headers
        if "SIGNIFY-RESOURCE" not in headers:
            raise ValueError("Missing signify resource header")

        return headers["SIGNIFY-RESOURCE"]

    def verify(self, req):
        print(f"verifying req {req}")

        headers = req.headers
        if "SIGNATURE-INPUT" not in headers or "SIGNATURE" not in headers:
            return False

        siginput = headers["SIGNATURE-INPUT"]
        if not siginput:
            return False
        signature = headers["SIGNATURE"]
        if not signature:
            return False

        inputs = ending.desiginput(siginput.encode("utf-8"))
        inputs = [i for i in inputs if i.name == "signify"]

        if not inputs:
            return False

        result="{'status_code': 404, 'text': '{\"title\": \"404 Not Found\", \"description\": \"No result\"}', 'headers': {'Content-Type': 'application/json'}}"
        for inputage in inputs:
            items = []
            for field in inputage.fields:
                if field.startswith("@"):
                    if field == "@method":
                        items.append(f'"{field}": {req.method}')
                    elif field == "@path":
                        items.append(f'"{field}": {req.path}')

                else:
                    key = field.upper()
                    field = field.lower()
                    if key not in headers:
                        continue

                    value = ending.normalize(headers[key])
                    items.append(f'"{field}": {value}')

            values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
            if inputage.expires is not None:
                values.append(f"expires={inputage.expires}")
            if inputage.nonce is not None:
                values.append(f"nonce={inputage.nonce}")
            if inputage.keyid is not None:
                values.append(f"keyid={inputage.keyid}")
            if inputage.context is not None:
                values.append(f"context={inputage.context}")
            if inputage.alg is not None:
                values.append(f"alg={inputage.alg}")

            params = ';'.join(values)

            items.append(f'"@signature-params: {params}"')
            ser = "\n".join(items).encode("utf-8")

            resource = self.resource(req)

            signages = ending.designature(signature)
            cig = signages[0].markers[inputage.name]

            result = verify_req(req,cig.raw,ser)
            print(f"AuthSigs.on_post: result {result}")
            if result['status_code'] > 300:
                return result

        return result

verSig = AuthSigs()

class LoginTask(object):

    def on_post(self, req, resp):
        print("LoginTask.on_post")
        try:
            raw_json = req.stream.read()
            data = json.loads(raw_json)
            print(f"LoginTask.on_post: sending data {str(data)[:50]}...")
            result = verify_vlei(data['aid'], data['said'], data['vlei'])
            # print(f"LoginTask.on_post: Will poll for result {result}")
            # while not result.ready():
            #     time.sleep(1)
            #     print(f"LoginTask.on_post: polling for result {result.id}")
            #     result = AsyncResult(result.id)  # Refresh the result object
            # result = result.get()
            print(f"LoginTask.on_post: received data {result['status_code']}")
            if(result["status_code"] < 400):
                print("Logged in user, checking status...")
                if(data['aid'] not in uploadStatus):
                    print("Added empty status for {}".format(data['aid']))
                    uploadStatus[data['aid']] = []
            resp.status = falcon.code_to_http_status(result["status_code"])
            resp.text = result["text"]
            resp.content_type = result["headers"]['Content-Type']
        except Exception as e:
            print(f"LoginTask.on_post: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
    def on_get(self, req, resp, aid):
        print("LoginTask.on_get")
        try:
            print(f"LoginTask.on_get: sending aid {aid}")
            result = check_login(aid)
            print(f"LoginTask.on_get: received data {result}")
            resp.status = falcon.code_to_http_status(result["status_code"])
            resp.text = result["text"]
            resp.content_type = result["headers"]['Content-Type']
        except Exception as e:
            print(f"LoginTask.on_get: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
class UploadTask(object):
        
    def on_post(self, req, resp, aid, dig):
        print("UploadTask.on_post {}".format(req))
        verSig.process_request(req, resp)
        try:
            raw = req.bounded_stream.read()
            # data = json.loads(raw)
            print(f"UploadTask.on_post: request for {aid} {dig} {raw} {req.content_type}")
            result = upload(aid, dig, req.content_type, raw)
            print(f"UploadTask.on_post: received data {result}")
            # while not result.ready():
            #     time.sleep(1)
            #     print(f"LoginTask.on_post: polling for result {result.id}")
            #     result = AsyncResult(result.id)  # Refresh the result object
            # result = result.get()
            resp.status = falcon.code_to_http_status(result["status_code"])
            resp.text = result["text"]
            resp.content_type = result["headers"]['Content-Type']
            # add to status dict
            if(aid not in uploadStatus):
                print(f"UploadTask.on_post: Error aid not logged in {aid}")
                resp.text = f"AID not logged in: {aid}"
                resp.status = falcon.HTTP_401    
            else:    
                print(f"UploadTask.on_post added uploadStatus for {aid}: {dig}")
                uploadStatus[f"{aid}"].append(resp.text)
        except Exception as e:
            print(f"UploadTask.on_post: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500
            
    def on_get(self, req, resp, aid, dig):
        print("UploadTask.on_get")
        verSig.process_request(req, resp)
        try:
            # raw_json = req.stream.read()
            # data = json.loads(raw_json)
            print(f"UploadTask.on_get: sending aid {aid} for dig {dig}")
            result = check_upload(aid, dig)
            print(f"UploadTask.on_get: received data {result}")
            resp.status = falcon.code_to_http_status(result["status_code"])
            resp.text = result["text"]
            resp.content_type = result["headers"]['Content-Type']
        except Exception as e:
            print(f"UploadTask.on_get: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500

class StatusTask(object):   
             
    def on_get(self, req, resp, aid):
        print(f"StatusTask.on_get request ")
        verSig.process_request(req, resp)
        try:
            # raw_json = req.stream.read()
            # data = json.loads(raw_json)
            print(f"StatusTask.on_get: aid {aid}")
            if(aid not in uploadStatus):
                print(f"UploadTask.on_post: Cannot find status for {aid}")
                resp.text = f"AID not logged in: {aid}"
                resp.status = falcon.HTTP_401
            else:
                result = uploadStatus[f"{aid}"]
                print(f"StatusTask.on_get: received data {result}")
                resp.status = falcon.HTTP_200
                resp.text = json.dumps({f"{aid}":result})
                if not result:
                    # no headers
                    print(f"Empty upload status list for aid {aid}")
        except Exception as e:
            print(f"StatusTask.on_get: Exception: {e}")
            resp.text = f"Exception: {e}"
            resp.status = falcon.HTTP_500

class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, text='\n')

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

# {
#     'HOST': 'localhost:8000', 
#     'CONNECTION': 'keep-alive', 
#     'CONTENT-LENGTH': '0', 
#     'SEC-CH-UA': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"', 
#     'SIGNIFY-RESOURCE': 'EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei', 
#     'SEC-CH-UA-MOBILE': '?0', 
#     'SIGNATURE-INPUT': 'signify=("signify-resource" "@method" "@path" "signify-timestamp");created=1689021741;keyid="EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei";alg="ed25519"', 
#     'USER-AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36', 
#     'ACCEPT': 'application/json', 
#     'SIGNATURE': 'indexed="?0";signify="0BDQ4PhhM6N6QuphJqVLHYnKDgyCxgFa6wMDVhCH2jRYpZcB8zozvpUL74GPVbxSa6A6LD5fYtFwsQ_dce9X90wA"', 'SEC-CH-UA-PLATFORM': '"macOS"', 
#     'ORIGIN': 'http://localhost:8000', 
#     'SEC-FETCH-SITE': 'same-origin', 
#     'SEC-FETCH-MODE': 'cors', 
#     'SEC-FETCH-DEST': 'empty', 
#     'REFERER': 'http://localhost:8000/api/doc', 
#     'ACCEPT-ENCODING': 'gzip, deflate, br', 
#     'ACCEPT-LANGUAGE': 'en-US,en;q=0.9'}
# post response {"title": "404 Not Found", "description": "unknown EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei used to sign header"}
# serializing response {'status_code': 404, 'text': '{"title": "404 Not Found", "description": "unknown EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei used to sign header"}', 'headers': {'Content-Type': 'application/json'}}

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
                    "/upload/{aid}/{dig}":{"post":{"tags":["default"],
                                        "summary":"Given an AID and DIG, returns information about the upload",
                                        "parameters":[{"in":"path","name":"aid","required":"true","schema":{"type":"string","minimum":1,"example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},"description":"The AID"},
                                                      {"in":"path","name":"dig","required":"true","schema":{"type":"string","minimum":1,"example":"EAPHGLJL1s6N4w1Hje5po6JPHu47R9-UoJqLweAci2LV"},"description":"The digest of the upload"}],
                                        "requestBody":{"required":"true","content":{"multipart/form-data":{"schema":{"type":"object","properties":{
                                            "upload":{"type":"string","format":"binary","example":f"{report_zip}"}
                                            }}}}},
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{
                                                                "submitter": "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk",
                                                                "filename": "test_report.zip",
                                                                "status": "failed",
                                                                "contentType": "application/zip",
                                                                "size": 3390,
                                                                "message": "No signatures found in manifest file"
                                                                }}}}}},
                                        }},
                    "/checkupload/{aid}/{dig}":{"get":{"tags":["default"],
                                        "summary":"Given an AID and DIG returns information about the upload status",
                                        "parameters":[{"in":"path","name":"aid","required":"true","schema":{"type":"string","minimum":1,"example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},"description":"The AID"},
                                                      {"in":"path","name":"dig","required":"true","schema":{"type":"string","minimum":1,"example":"EAPHGLJL1s6N4w1Hje5po6JPHu47R9-UoJqLweAci2LV"},"description":"The digest of the upload"}],
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{
                                                                "submitter": "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk",
                                                                "filename": "DUMMYLEI123456789012.IND_FR_IF010200_IFTM_2022-12-31_20220222134211000.zip",
                                                                "status": "failed",
                                                                "contentType": "application/zip",
                                                                "size": 3390,
                                                                "message": "No signatures found in manifest file"
                                        }}}}}},
                                        }},
                    "/status/{aid}":{"get":{"tags":["default"],
                                        "summary":"Given an AID returns information about the upload status",
                                        "parameters":[
                                            {"in":"header","name":"Signature","required":"true",
                                             "schema":{"type":"string","example":"indexed=\"?0\";signify=\"0BDQ4PhhM6N6QuphJqVLHYnKDgyCxgFa6wMDVhCH2jRYpZcB8zozvpUL74GPVbxSa6A6LD5fYtFwsQ_dce9X90wA\""},
                                             "description":"The signature of the data"},
                                            {"in":"header","name":"Signature-Input","required":"true",
                                             "schema":{"type":"string","example":"signify=(\"signify-resource\" \"@method\" \"@path\" \"signify-timestamp\");created=1689021741;keyid=\"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei\";alg=\"ed25519\""},
                                             "description":"The signature of the data"},
                                            {"in":"header","name":"Signify-Resource","required":"true",
                                             "schema":{"type":"string","example":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"},
                                             "description":"The signature of the data"},
                                            {"in":"path","name":"aid","required":"true",
                                             "schema":{"type":"string","minimum":1,"example":"EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"},
                                             "description":"The AID"}
                                        ],
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":[{
                                                                "submitter": "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk",
                                                                "filename": "DUMMYLEI123456789012.IND_FR_IF010200_IFTM_2022-12-31_20220222134211000.zip",
                                                                "status": "failed",
                                                                "contentType": "application/zip",
                                                                "size": 3390,
                                                                "message": "No signatures found in manifest file"
                                        }]}}}}},
                                        }},
                    "/verify/header":{"post":{"tags":["default"],
                                        "summary":"Given an AID, returns if the headers are properly signed",
                                        "parameters":[
                                            {"in":"header","name":"Signature","required":"true",
                                             "schema":{"type":"string","example":"indexed=\"?0\";signify=\"0BDQ4PhhM6N6QuphJqVLHYnKDgyCxgFa6wMDVhCH2jRYpZcB8zozvpUL74GPVbxSa6A6LD5fYtFwsQ_dce9X90wA\""},
                                             "description":"The signature of the data"},
                                            {"in":"header","name":"Signature-Input","required":"true",
                                             "schema":{"type":"string","example":"signify=(\"signify-resource\" \"@method\" \"@path\" \"signify-timestamp\");created=1689021741;keyid=\"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei\";alg=\"ed25519\""},
                                             "description":"The signature of the data"},
                                            {"in":"header","name":"Signify-Resource","required":"true",
                                             "schema":{"type":"string","example":"EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"},
                                             "description":"The signature of the data"}
                                        ],
                                        "responses":{"200":{"description":"OK","content":{"application/json":{"schema":{"type":"object","example":{"status": "200 OK", "message": "AID and vLEI valid login"}}}}}},
                                        }},
                    }}

    doc = api_doc(app, config=config, url_prefix='/api/doc', title='API doc', editor=True)
    return doc

def falcon_app():    
    app = falcon.App(middleware=falcon.CORSMiddleware(
    allow_origins='*', allow_credentials='*',
    expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                    'signify-resource', 'signify-timestamp']))
    if os.getenv("ENABLE_CORS", "false").lower() in ("true", "1"):
        print("CORS  enabled")
        app.add_middleware(middleware=HandleCORS())
    # app.add_middleware(middleware=HandleSigs())
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    # app = falcon.asgi.App()
    app.add_route('/ping', PingResource())
    app.add_route('/login', LoginTask())
    app.add_route("/checklogin/{aid}", LoginTask())
    app.add_route('/upload/{aid}/{dig}', UploadTask())
    app.add_route("/checkupload/{aid}/{dig}", UploadTask())
    app.add_route("/status/{aid}", StatusTask())
    app.add_route("/verify/header", verSig)
    
    return app
    
def main():
    print("Starting RegPS...")
    app = falcon_app()
    api_doc=swagger_ui(app)

    return app
    
if __name__ == '__main__':
    main()