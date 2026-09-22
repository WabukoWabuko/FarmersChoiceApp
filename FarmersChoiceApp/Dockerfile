FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8550 DATABASE_PATH=/data/user_data.db RECOMMENDATION_DATABASE_PATH=/data/recommendation_data.db
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data
EXPOSE 8550
CMD ["python", "main.py"]
