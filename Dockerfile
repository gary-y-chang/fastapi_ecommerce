FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install python3-dev default-libmysqlclient-dev gcc  -y

RUN pip install --upgrade pip 
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 80