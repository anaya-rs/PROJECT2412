#!/bin/bash

# Production Startup Script for Project2412
echo "🚀 Starting Project2412 Production Environment..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose."
    exit 1
fi

# Set environment file
export COMPOSE_FILE="docker-compose.prod.yml"
export ENV_FILE=".env.production"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found. Please create it from .env.production.example"
    exit 1
fi

echo "📦 Building and starting containers..."

# Start services
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check backend health
BACKEND_HEALTH=$(curl -s http://localhost:5005/health | jq -r '.status' 2>/dev/null)
if [ "$BACKEND_HEALTH" = "healthy" ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

# Check frontend
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

# Check database
DB_HEALTH=$(curl -s http://localhost:5005/health/database | jq -r '.status' 2>/dev/null)
if [ "$DB_HEALTH" = "healthy" ]; then
    echo "✅ Database is connected"
else
    echo "❌ Database health check failed"
fi

# Check RAG service (if enabled)
RAG_HEALTH=$(curl -s http://localhost:5005/health/rag | jq -r '.status' 2>/dev/null)
if [ "$RAG_HEALTH" = "healthy" ]; then
    echo "✅ RAG service is connected"
elif [ "$RAG_HEALTH" = "disabled" ]; then
    echo "ℹ️ RAG service is disabled"
else
    echo "❌ RAG service health check failed"
fi

echo ""
echo "🎉 Project2412 is starting up!"
echo "📊 Frontend: http://localhost:8080"
echo "🔧 Backend API: http://localhost:5005"
echo "📖 API Docs: http://localhost:5005/docs"
echo ""
echo "📝 To view logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "🛑 To stop: docker-compose -f $COMPOSE_FILE down"
