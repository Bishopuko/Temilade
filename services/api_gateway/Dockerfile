FROM python:3.9-slim

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 8000

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
