FROM python:3-slim as build
LABEL maintainer="timothe{at}quango.fr"

WORKDIR /usr/src/imap2kb
COPY requirements.txt ./
RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get remove -y g++ && apt-get autoremove -y
ENV PYTHONUNBUFFERED=1
COPY . .
COPY ./config ./config

# Testing
FROM build as testing
RUN python test.py

# Actual image
FROM build
CMD [ "python", "./daemon.py" ]
