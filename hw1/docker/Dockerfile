FROM python:3.13-slim

RUN apt-get update && apt-get install -y vim curl dnsutils

WORKDIR /my-app

COPY ./my-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./my-app/app ./app

RUN mkdir -p ./app/logs

EXPOSE 5003

CMD ["python3", "app/main.py"]