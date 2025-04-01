FROM python:3.12.2-alpine3.19
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip install --no-cache -r requirements.txt
COPY . .
ENV PATH="/app/venv/bin:$PATH"
CMD ["uvicorn", "src.main:app", "--reload"]
  
