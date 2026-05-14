#!/bin/bash

# Set the image name
IMAGE_NAME="polaris-mcp"
CONTAINER_NAME="polaris-mcp"
NETWORK_NAME="local-iceberg"

podman network exists "$NETWORK_NAME" 2>/dev/null || podman network create "$NETWORK_NAME"

# Build the Docker image using Podman
podman build -f dockerfile.mcp -t $IMAGE_NAME .

# Stop and remove any existing container with the same name
podman stop $CONTAINER_NAME 2>/dev/null
podman rm $CONTAINER_NAME 2>/dev/null

# Run the Docker container using Podman
podman run \
  --rm \
  -p 8000:8000 \
  --env-file .env.development \
  --env POLARIS_CATALOG_URI="http://polaris-server:8181/api/catalog" \
  --network "$NETWORK_NAME" \
  -v $(pwd)/mcp/pydantic_models.py:/app/pydantic_models.py \
  -v $(pwd)/mcp/main.py:/app/main.py \
  -v $(pwd)/mcp/utils.py:/app/utils.py \
  --name $CONTAINER_NAME \
  $IMAGE_NAME

echo "Podman container $CONTAINER_NAME is running."
