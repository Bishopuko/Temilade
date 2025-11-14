FROM python:3.9-slim

WORKDIR /t

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Run migrations and start Django server
EXPOSE 8081
CMD ["python", "templates/manage.py", "runserver", "0.0.0.0:8081"]
