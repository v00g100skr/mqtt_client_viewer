FROM python:3.13.3-alpine

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Copy application code
COPY viewer.py .

# Expose port
EXPOSE 8080

# Run with uvicorn
CMD ["uvicorn", "viewer:app", "--host", "0.0.0.0", "--port", "8080"]
