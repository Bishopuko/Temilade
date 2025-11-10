# Stage 4 Backend Task: Distributed Notification System

## Overview

Build a notification system that sends emails and push notifications using separate microservices. Each service should communicate asynchronously through a message queue (RabbitMQ).

## Services to Build

1. **API Gateway Service** (Python/Django) - Entry point for all notification requests
2. **User Service** (C#) - Manages user contact info and preferences
3. **Email Service** (Node.js/Fastify) - Sends emails via SMTP/API
4. **Push Service** (Node.js/Fastify) - Sends push notifications
5. **Template Service** (PHP) - Manages notification templates

## Key Requirements

- Asynchronous communication via RabbitMQ
- Health checks for all services
- Idempotency and retry mechanisms
- Circuit breaker pattern
- Proper error handling and logging
- Docker containerization
- CI/CD pipeline

## Current Status

- [x] Project structure set up
- [x] Docker Compose configuration
- [x] Basic service skeletons
- [x] RabbitMQ queue setup in API Gateway
- [x] Complete API Gateway implementation
- [ ] User Service implementation
- [ ] Email Service implementation
- [ ] Push Service implementation
- [ ] Template Service implementation
- [ ] Integration testing
- [ ] CI/CD deployment

## Detailed Implementation Steps by Service

### 1. API Gateway Service (Python/Django) - Team Member 1

**Current Progress**: Basic structure and queue setup done.

**Next Steps**:

- [ ] Complete the `send_notification` endpoint with proper validation
- [ ] Add authentication/authorization middleware
- [ ] Implement status tracking for notifications (store in Redis/PostgreSQL)
- [ ] Add GET endpoint to check notification status by request_id
- [ ] Implement idempotency check using Redis
- [ ] Add request/response logging with correlation IDs
- [ ] Create OpenAPI/Swagger documentation
- [ ] Add rate limiting using Redis
- [ ] Implement circuit breaker for downstream service calls
- [ ] Add comprehensive error handling and response formatting
- [ ] Write unit tests for all endpoints
- [ ] Performance optimization for <100ms response time

**Key Files to Work On**:

- `services/api_gateway/src/api_gateway/views.py` - Complete notification endpoints
- `services/api_gateway/src/api_gateway/urls.py` - Add new URL patterns
- `services/api_gateway/src/notification_system/settings.py` - Add database/cache configs
- `services/api_gateway/requirements.txt` - Add necessary dependencies (pika, redis, requests)

### 2. User Service (C#) - Team Member 2

**Current Progress**: Basic C# project structure.

**Next Steps**:

- [ ] Set up ASP.NET Core Web API project
- [ ] Create PostgreSQL database models for users, preferences, tokens
- [ ] Implement Entity Framework Core for data access
- [ ] Create REST API endpoints:
  - POST /users - Create user
  - GET /users/{id} - Get user details
  - PUT /users/{id}/preferences - Update notification preferences
  - POST /users/{id}/tokens - Add push tokens
  - GET /users/{id}/contact - Get contact info for notifications
- [ ] Add JWT authentication and authorization
- [ ] Implement Redis caching for user preferences
- [ ] Add input validation and error handling
- [ ] Implement pagination for user lists
- [ ] Add health check endpoint (/health)
- [ ] Create OpenAPI/Swagger documentation
- [ ] Write unit and integration tests
- [ ] Add logging with correlation IDs

**Key Files to Work On**:

- `services/user_service/UserService.csproj` - Update project file
- `services/user_service/Program.cs` - Configure services and middleware
- Create `Controllers/UsersController.cs`
- Create `Models/User.cs`, `Models/Preference.cs`, etc.
- Create `Data/ApplicationDbContext.cs`
- Update `services/user_service/Dockerfile` if needed

### 3. Email Service (Node.js/Fastify) - Team Member 3

**Current Progress**: Basic Fastify server with health endpoint.

**Next Steps**:

- [ ] Install additional dependencies: amqplib, nodemailer, redis
- [ ] Create RabbitMQ consumer for `email.queue`
- [ ] Implement message processing:
  - Parse message (request_id, user_id, template_id, variables)
  - Fetch user contact info from User Service (REST call)
  - Fetch template from Template Service (REST call)
  - Substitute variables in template
  - Send email via SMTP (Gmail/SendGrid)
- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker for SMTP failures
- [ ] Handle delivery confirmations and bounces
- [ ] Store notification status in Redis
- [ ] Add idempotency check using request_id
- [ ] Implement dead-letter publishing for permanent failures
- [ ] Add comprehensive error handling and logging
- [ ] Create email templates for different notification types
- [ ] Write unit tests for message processing
- [ ] Add monitoring/metrics (message processing rate, success rate)

**Key Files to Work On**:

- `services/email_service/index.js` - Implement consumer and email sending logic
- `services/email_service/package.json` - Add dependencies
- Create `src/consumer.js` - RabbitMQ consumer logic
- Create `src/emailService.js` - Email sending logic
- Create `src/templateProcessor.js` - Variable substitution

### 4. Push Service (Node.js/Fastify) - Team Member 4

**Current Progress**: Basic Fastify server with health endpoint.

**Next Steps**:

- [ ] Install additional dependencies: amqplib, fcm-node or web-push, redis
- [ ] Create RabbitMQ consumer for `push.queue`
- [ ] Implement message processing:
  - Parse message (request_id, user_id, template_id, variables)
  - Fetch user push tokens from User Service (REST call)
  - Fetch template from Template Service (REST call)
  - Substitute variables in template
  - Send push notification via FCM/OneSignal/Web Push
- [ ] Implement retry logic with exponential backoff
- [ ] Add circuit breaker for FCM/OneSignal failures
- [ ] Validate device tokens and handle invalid tokens
- [ ] Support rich notifications (title, text, image, link)
- [ ] Store notification status in Redis
- [ ] Add idempotency check using request_id
- [ ] Implement dead-letter publishing for permanent failures
- [ ] Add comprehensive error handling and logging
- [ ] Write unit tests for message processing
- [ ] Add monitoring/metrics (message processing rate, success rate)

**Key Files to Work On**:

- `services/push_service/index.js` - Implement consumer and push sending logic
- `services/push_service/package.json` - Add dependencies
- Create `src/consumer.js` - RabbitMQ consumer logic
- Create `src/pushService.js` - Push notification sending logic
- Create `src/templateProcessor.js` - Variable substitution

### 5. Template Service (PHP) - Team Member 1/2 (Shared)

**Current Progress**: Basic PHP project structure.

**Next Steps**:

- [ ] Set up Slim framework or plain PHP
- [ ] Create PostgreSQL database schema for templates and versions
- [ ] Implement REST API endpoints:
  - POST /templates - Create template
  - GET /templates/{id} - Get template by ID
  - PUT /templates/{id} - Update template
  - GET /templates/{id}/versions - Get template versions
  - POST /templates/{id}/render - Render template with variables
- [ ] Implement variable substitution logic ({{variable}})
- [ ] Add support for multiple languages/locales
- [ ] Implement version history tracking
- [ ] Add input validation and error handling
- [ ] Implement Redis caching for frequently used templates
- [ ] Add health check endpoint (/health)
- [ ] Create OpenAPI/Swagger documentation
- [ ] Write unit tests
- [ ] Add logging with correlation IDs

**Key Files to Work On**:

- `services/template_service/composer.json` - Add dependencies
- `services/template_service/public/index.php` - Implement API endpoints
- Create database migration files
- Create `src/TemplateController.php`
- Create `src/TemplateProcessor.php`

## Integration and Testing Phase

- [ ] Set up end-to-end testing with all services
- [ ] Test message flow: API Gateway → Queue → Consumer → External API
- [ ] Performance testing (1000+ notifications/min)
- [ ] Load testing for horizontal scaling
- [ ] Failure scenario testing (service down, network issues)
- [ ] Update system design diagram with final architecture

## CI/CD and Deployment

- [ ] Complete GitHub Actions workflow
- [ ] Add automated testing in CI/CD
- [ ] Configure deployment to server
- [ ] Add monitoring and alerting
- [ ] Create runbooks for operations

## Final Deliverables

- [ ] Working notification system
- [ ] System design diagram
- [ ] API documentation
- [ ] Performance test results
- [ ] Demo presentation
