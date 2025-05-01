FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY wait-for-it.sh .

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x wait-for-it.sh

COPY . .

#ENTRYPOINT []
CMD ["python", "scraper.py"]