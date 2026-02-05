FROM python:3.10-slim

WORKDIR /app

# FIX: Install system dependencies (git)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=flask_app.py

CMD ["flask", "run", "--host=0.0.0.0"]
