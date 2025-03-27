FROM python:3.12.2-alpine3.19
COPY requirements.txt .
RUN python3 -m 