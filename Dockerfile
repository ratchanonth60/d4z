FROM python:3.13-alpine 


WORKDIR /fastapi
RUN apk add --no-cache \
  build-base \
  postgresql-dev \
  libffi-dev \
  postgresql-client

# Copy requirements.txt และติดตั้ง Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /fastapi/app
