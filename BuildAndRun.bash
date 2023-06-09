#!/bin/bash

# Define variables
IMAGE_NAME="etl-api"
CONTAINER_NAME="my-container"

# Build the Docker image
docker build -t "$IMAGE_NAME" .

# Run the Docker container
docker-compose up --build
