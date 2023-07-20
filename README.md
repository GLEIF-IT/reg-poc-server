# reg-poc-server
A service to manage regulator portal requests/responses that require authentication, document submission and validation. 

## Architecture

### Server (this service)
Provides the ability to:
* Log in using a vLEI ECR
* Upload signed files
* Check the status of an upload

In two seperate terminals run:

```
cd src/regps; celery -A app.tasks worker -l DEBUG
```

and

```
cd src/regps; gunicorn -b 0.0.0.0:8000 app:app --reload
```

Requires a running [Redis](https://redis.io/) instance on the default port. 

### Webapp
The web app (UI front-end) uses Signify/KERIA for selecting identifiers and credentials:
See: [reg-poc-webapp](https://github.com/GLEIF-IT/reg-poc-webapp)

### Verifier
The verifier uses [keripy](https://github.com/WebOfTRust/keripy) for verifying the requets:
See: [reg-poc-verifier](https://github.com/GLEIF-IT/reg-poc-verifier)

### Additional service
* KERI Witness Network
* vLEI server
* KERI Agent

The deployment architecture is demonstrated in [reg-poc](https://github.com/GLEIF-IT/reg-poc)

#### REST API
 You can run a test query using Swagger by going to:
 ```
 http://127.0.0.1:8000/api/doc#
 ```

