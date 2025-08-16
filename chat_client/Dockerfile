FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY chat_client /app/chat_client
EXPOSE 8000
CMD ["uvicorn","chat_client.api.main:app","--host","0.0.0.0","--port","8000"]
