#!/bin/bash

set -a; source .env.development; set +a

# Set the image name
IMAGE_NAME="polaris-postgres"
CONTAINER_NAME="polaris-postgres"
NETWORK_NAME="local-iceberg"

podman network exists "$NETWORK_NAME" 2>/dev/null || podman network create "$NETWORK_NAME"

# Build the Docker image using Podman
podman build -f dockerfile.db -t $IMAGE_NAME .

# Check if the build was successful
if [[ $? -ne 0 ]]; then
  echo "Error: Podman build failed!"
  exit 1
fi

# Stop and remove any existing container with the same name
podman stop $CONTAINER_NAME 2>/dev/null
podman rm $CONTAINER_NAME 2>/dev/null

# Run the Docker container using Podman
podman run \
  --rm \
  --env POSTGRES_DB="polaris" \
  --env POSTGRES_USER="$QUARKUS_DATASOURCE_USERNAME" \
  --env POSTGRES_PASSWORD="$QUARKUS_DATASOURCE_PASSWORD" \
  -v "$ICEBERG_WAREHOUSE_HOST":"/data/iceberg-lake":Z \
  --network "$NETWORK_NAME" \
  -p 5432:5432 \
  --name $CONTAINER_NAME \
  $IMAGE_NAME

# Check if the container started successfully
if [[ $? -ne 0 ]]; then
  echo "Error: Podman run failed!"
  exit 1
fi
