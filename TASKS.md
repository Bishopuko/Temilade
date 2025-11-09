# Team Tasks and Tickets

## Team Members and Assignments

Assuming team of 4:

- Member 1: Python/Django (API Gateway)
- Member 2: C# (User Service)
- Member 3: Node.js (Email Service)
- Member 4: PHP (Push Service and Template Service)

## Tickets

### API Gateway Service (Member 1 - Python/Django)

- [ ] Set up Django project structure
- [ ] Implement request validation and authentication
- [ ] Route messages to email/push queues
- [ ] Track notification status
- [ ] Add /health endpoint
- [ ] Implement circuit breaker
- [ ] Add idempotency with unique IDs
- [ ] Write unit tests
- [ ] Create OpenAPI docs
- [ ] Dockerize the service

### User Service (Member 2 - C#)

- [ ] Set up ASP.NET Core project
- [ ] Implement user model (email, push_tokens, preferences)
- [ ] Add REST APIs for user data
- [ ] Handle login and permissions
- [ ] Integrate PostgreSQL
- [ ] Add /health endpoint
- [ ] Implement caching with Redis
- [ ] Write unit tests
- [ ] Create OpenAPI docs
- [ ] Dockerize the service

### Email Service (Member 3 - Node.js)

- [ ] Set up Node.js project (not Express, e.g., Fastify or Koa)
- [ ] Consume messages from email.queue
- [ ] Implement template filling with variables
- [ ] Send emails via SMTP/API (e.g., SendGrid)
- [ ] Handle delivery confirmations and bounces
- [ ] Add retry with exponential backoff
- [ ] Add /health endpoint
- [ ] Write unit tests
- [ ] Create OpenAPI docs
- [ ] Dockerize the service

### Push Service (Member 4 - PHP)

- [ ] Set up PHP project (e.g., Slim or Lumen)
- [ ] Consume messages from push.queue
- [ ] Send push notifications (e.g., FCM, OneSignal)
- [ ] Validate device tokens
- [ ] Support rich notifications
- [ ] Add retry with exponential backoff
- [ ] Add /health endpoint
- [ ] Write unit tests
- [ ] Create OpenAPI docs
- [ ] Dockerize the service

### Template Service (Member 4 - PHP)

- [ ] Set up PHP project (shared or separate)
- [ ] Implement template storage (PostgreSQL)
- [ ] Handle variable substitution
- [ ] Support multiple languages
- [ ] Keep version history
- [ ] Add REST APIs
- [ ] Add /health endpoint
- [ ] Write unit tests
- [ ] Create OpenAPI docs
- [ ] Dockerize the service

### Shared Tasks

- [ ] Set up RabbitMQ exchange and queues
- [ ] Configure PostgreSQL and Redis in docker-compose
- [ ] Implement shared libraries if needed
- [ ] Set up monitoring and logging
- [ ] Create system design diagram
- [ ] Write CI/CD workflow
- [ ] Test end-to-end integration
- [ ] Performance testing (1000+ notifications/min)
- [ ] Documentation

## Progress Tracking

Update this file with [x] when tasks are completed.
