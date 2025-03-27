FROM python:3.12.2-alpine3.19
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv --without-pip venv
RUN pip install --no-cache --target="venv/lib/python3.12/site-packages" -r requirements.txt
COPY . .

CMD ["python", "-m", "src.main"]
