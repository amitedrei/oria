#!/bin/bash

cd frontend && npm run build
mkdir ../backend/oria_backend/static && cp -r build/* ../backend/oria_backend/static/
cd ../backend && docker build --platform linux/amd64  -t test-backend .
