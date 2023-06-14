# regulation-portal-service
A service to manage regulator portal requests/responses that requires authentication, document submission, validation, and more 

## Desgin
### Web app support
The web app (UI front-end) will be using Signify/KERIA for selecting identifiers and credentials:

### This service
The regulation service will provide the ability to:
* Login using an AID, SAID, and vLEI
* Upload signed files
* Check the status of an upload

## Development
You need to run a local vLEI service, see https://github.com/GLEIF-IT/reg-poc-verifier:
```verifier server start --config-dir scripts --config-file verifier-config.json```

To start this web service:
```docker-compose up -d --build```
To tear this web service:
```docker-compose down```

You should see:
```[+] Running 4/4
 ✔ Network reg-poc-server_default     Created                                                                                                                                                                                                                                                                 0.1s 
 ✔ Container reg-poc-server-redis-1   Started                                                                                                                                                                                                                                                                 0.6s 
 ✔ Container web                      Started                                                                                                                                                                                                                                                                 0.8s 
 ✔ Container reg-poc-server-celery-1  Started
 ```

 You can run a test query using Swagger by going to:
 ```
 http://127.0.0.1:8000/api/doc#
 ```

