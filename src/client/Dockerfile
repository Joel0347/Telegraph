FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["streamlit", "run", "main.py", "--server.port=5000", "--server.address=0.0.0.0"]
