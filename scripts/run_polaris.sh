#!/bin/bash

# Load env
set -a; source .env.development; set +a

# Set the container/network name
CONTAINER_NAME="polaris-server"
NETWORK_NAME="local-iceberg"

podman network exists "$NETWORK_NAME" 2>/dev/null || podman network create "$NETWORK_NAME"

# Stop and remove any existing container with the same name
podman stop $CONTAINER_NAME 2>/dev/null
podman rm $CONTAINER_NAME 2>/dev/null

# Run the Docker container using Podman
podman run \
  --rm \
  --env="QUARKUS_DATASOURCE_USERNAME=$QUARKUS_DATASOURCE_USERNAME" \
  --env="QUARKUS_DATASOURCE_PASSWORD=$QUARKUS_DATASOURCE_PASSWORD" \
  --env="QUARKUS_DATASOURCE_JDBC_URL=$QUARKUS_DATASOURCE_JDBC_URL" \
  --network "$NETWORK_NAME" \
  -p 8181:8181 \
  -p 8182:8182 \
  -v "$ICEBERG_WAREHOUSE_HOST":"/data/iceberg-lake":Z \
  -v "$(pwd)/config/application-local.properties:/deployments/config/application.properties:Z" \
  --name $CONTAINER_NAME \
  apache/polaris:latest

# Check if the container started successfully
if [[ $? -ne 0 ]]; then
  echo "Error: Podman run failed!"
  exit 1
fi
