FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Expose the mandatory Hugging Face port
EXPOSE 7860

CMD [ "uvicorn", "server.api_server:app", "--host", "0.0.0.0", "--port", "7860" ]