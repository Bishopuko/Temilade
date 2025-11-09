# System Architecture

## Overview

The Distributed Notification System is built using a microservices architecture with asynchronous communication via message queues.

## Services

- **API Gateway**: Entry point, validates requests, routes to queues.
- **User Service**: Manages users, preferences.
- **Email Service**: Sends emails.
- **Push Service**: Sends push notifications.
- **Template Service**: Manages templates.

## Message Queue (RabbitMQ)

- Exchange: notifications.direct
- Queues:
  - email.queue -> Email Service
  - push.queue -> Push Service
  - failed.queue -> Dead Letter Queue

## Data Flow

1. Client sends request to API Gateway.
2. Gateway validates, publishes to queue.
3. Consumer service processes message, sends notification.
4. Status updates via shared store.

## Failure Handling

- Circuit Breaker: Prevents cascading failures.
- Retry: Exponential backoff, dead-letter queue.
- Idempotency: Unique request IDs.

## Scaling

- Horizontal scaling for all services.
- Load balancing via API Gateway.
- Queue partitioning if needed.

## Diagram

[Insert diagram here - use Draw.io/Miro]

Service Connections:

- API Gateway -> RabbitMQ
- Services -> PostgreSQL/Redis
- Synchronous calls: Gateway -> User/Template Services

Queue Structure:

- Direct exchange with routing keys.

Retry Flow:

- Failed messages -> retry queue -> dead-letter if permanent failure.
