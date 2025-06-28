#!/bin/bash
CONTAINER_NAME="oria-backend"
IMAGE_NAME="oria-backend"

cd frontend && npm install && npm run build
mkdir ../backend/oria_backend/static
rm -rf ../backend/oria_backend/static/*
cp -r build/* ../backend/oria_backend/static/

if [ "$(docker ps -a -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Container $CONTAINER_NAME already exists. Removing it..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
    docker rmi $IMAGE_NAME 2>/dev/null || true
fi

cd ../backend && DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t $IMAGE_NAME .

echo "Creating new container: $CONTAINER_NAME"
docker run -d --name $CONTAINER_NAME -p 80:8000 $IMAGE_NAME

echo "Container $CONTAINER_NAME successfully created and running."