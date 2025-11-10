# TODO: Convert Push and Email Services to Use Fastify

## Push Service Conversion

- [x] Delete services/push_service/composer.json
- [x] Delete services/push_service/public/index.php
- [x] Create services/push_service/package.json with Fastify dependency
- [x] Create services/push_service/index.js with Fastify server and health endpoint on port 8080
- [x] Update services/push_service/Dockerfile to use Node.js

## Email Service Conversion

- [x] Update services/email_service/package.json to replace Express with Fastify
- [x] Update services/email_service/index.js to use Fastify instead of Express
