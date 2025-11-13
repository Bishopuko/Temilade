#!/bin/bash

# Exit immediately if a command fails
set -e

# Print commands as they run (optional, for debugging)
set -x

# Build and start all services defined in docker-compose.yml
docker compose up --build
