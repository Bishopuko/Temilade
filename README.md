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
2. Run `docker-compose up` in the docker/ directory.
3. Each service has its own setup (see service READMEs).

## Team Assignments

See TASKS.md for detailed tasks per member.

## CI/CD

GitHub Actions workflow for automated testing and deployment.

## Submission

Use /submit command in channel. Deadline: Nov 12, 2025, 11:59pm WAT.
