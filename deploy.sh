#!/bin/bash
set -e  # exit on error

APP_DIR='/home/ai/growlab'
COMPOSE_FILE='docker-compose.yml'
REPO_URL='git@github.com:Classimind/growlab_backend.git'  

# Create app directory if missing
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Pull or clone repo
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    git clone $REPO_URL .
else
    echo "Pulling latest changes..."
    git pull origin main
fi

# Build and run containers
echo "Starting Docker Compose services..."
docker-compose -f $COMPOSE_FILE up -d --build

# Clean up unused images
docker-compose down --rmi local

echo "Deployment completed!"
