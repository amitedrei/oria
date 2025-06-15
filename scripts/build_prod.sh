#!/bin/bash
CONTAINER_NAME="oria-backend-test"

cd frontend && npm install && npm run build
mkdir ../backend/oria_backend/static
rm -rf ../backend/oria_backend/static/*
cp -r build/* ../backend/oria_backend/static/

if [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Container $CONTAINER_NAME already exists. Removing it..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    docker rmi new-test-backend 2>/dev/null || true
fi

cd ../backend && DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t new-test-backend .

echo "Creating new container: $CONTAINER_NAME"
docker run -d --name $CONTAINER_NAME -p 1337:8000 new-test-backend

echo "Container $CONTAINER_NAME successfully created and running."