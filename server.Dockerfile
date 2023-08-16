FROM python:3.10.4-alpine3.16

WORKDIR /server
COPY ./ ./ 
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /server/src/regps
ENV KERI_AGENT_CORS=true

ENTRYPOINT [ "gunicorn", "-b", ":8000", "app:app"]
