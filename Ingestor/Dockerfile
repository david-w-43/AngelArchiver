FROM python:3.9-alpine

ADD angel_ingestor.py .

RUN pip install beautifulsoup4 datetime requests mysql.connector

CMD ["python", "angel_ingestor.py"]
