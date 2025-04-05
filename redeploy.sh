#!/bin/bash

# Default values
HA_TOKEN=""
HA_HOST=""
CONTAINER_PORT=8080

# Check for arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--ha-token)
            HA_TOKEN="$2"
            shift 2
            ;;
        -h|--ha-host)
            HA_HOST="$2"
            shift 2
            ;;
        -p|--container-port)
            CONTAINER_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

echo "HA_TOKEN: $HA_TOKEN"
echo "HA_HOST: $HA_HOST"
echo "CONTAINER_PORT: $CONTAINER_PORT"

# Updating the Git repo
echo "Updating Git repo..."
#cd /path/to/your/git/repo
git pull

# Moving to the deployment directory
echo "Moving to deployment directory..."
#cd /deploy/tcp_server

# Building Docker image
echo "Building Docker image..."
docker build -t home_assistant_viewer -f Dockerfile .

# Stopping and removing the old container (if exists)
echo "Stopping and removing old container..."
docker stop home_assistant_viewer || true
docker rm home_assistant_viewer || true

# Deploying the new container
echo "Deploying new container..."
docker run --name home_assistant_viewer --restart unless-stopped -d -p 8080:"$CONTAINER_PORT"  --env HA_TOKEN="$HA_TOKEN" --env HA_HOST="$HA_HOST" home_assistant_viewer

echo "Container deployed successfully!"

