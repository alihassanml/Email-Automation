# Use Python base image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8100"]
