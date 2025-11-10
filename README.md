# Distributed Notification System

A microservices-based notification system that sends emails and push notifications asynchronously using message queues.

## Overview

This project implements a distributed notification system with the following services:

- **API Gateway Service**: Entry point for requests, validation, routing to queues.
- **User Service**: Manages user data, preferences, authentication.
- **Email Service**: Processes email notifications from queue.
- **Push Service**: Handles push notifications.
- **Template Service**: Manages notification templates.

## Architecture

- **Message Queue**: RabbitMQ (with exchanges: notifications.direct, queues: email.queue, push.queue, failed.queue)
- **Databases**: PostgreSQL for services, Redis for caching.
- **Communication**: Synchronous via REST, Asynchronous via queues.
- **Containerization**: Docker with docker-compose for local development.

## Tech Stack

- Languages: Python (Django), C#, Node.js, PHP
- Queue: RabbitMQ
- DB: PostgreSQL + Redis
- Container: Docker
- API Docs: OpenAPI/Swagger

## Setup

1. Clone the repo.
2. Copy `.env.example` to `.env` and configure environment variables.
3. Run `docker-compose up` in the docker/ directory to start all services.
4. Services will be available at:
   - API Gateway: http://localhost:8000
   - User Service: http://localhost:5000
   - Email Service: http://localhost:3000
   - Push Service: http://localhost:8080
   - Template Service: http://localhost:8081
   - RabbitMQ Management: http://localhost:15672
5. Each service has a `/health` endpoint for status checks.

## Team Assignments

See TASKS.md for detailed tasks per member.

## CI/CD

GitHub Actions workflow for automated testing and deployment.
