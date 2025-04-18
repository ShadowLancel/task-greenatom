FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

COPY . .