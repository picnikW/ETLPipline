FROM python:3.9

WORKDIR /etl-api

COPY requirements.txt .
COPY ./src ./src

RUN pip install -r requirements.txt
EXPOSE 8000

CMD ["python", "./src/app.py"]