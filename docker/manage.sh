#!/bin/bash

# Docker management script for RAG System
# This script provides convenient commands to manage the Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================="
    echo "    RAG System Docker Manager"
    echo "=================================="
    echo -e "${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Run reference checks
check_references() {
    print_status "Running reference checks..."

    if [ -f "scripts/check_references.py" ]; then
        if command -v python3 > /dev/null 2>&1; then
            python3 scripts/check_references.py
            return $?
        else
            print_warning "Python3 not found. Skipping reference checks."
            return 0
        fi
    else
        print_warning "Reference checker not found. Skipping checks."
        return 0
    fi
}

# Build the Docker image
build() {
    print_status "Running pre-build reference checks..."
    if ! check_references; then
        print_error "Reference checks failed. Please fix the issues before building."
        exit 1
    fi

    print_status "Building RAG System Docker image..."
    docker-compose build --no-cache
    print_status "Build completed successfully!"
}

# Start the services
start() {
    print_status "Starting RAG System..."
    docker-compose up -d

    print_status "Waiting for services to be ready..."
    sleep 10

    # Check if the service is healthy
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "RAG System is running successfully!"
        print_status "Access the API at: http://localhost:8000"
        print_status "View API docs at: http://localhost:8000/docs"
    else
        print_warning "Service may still be starting up. Check logs with: $0 logs"
    fi
}

# Stop the services
stop() {
    print_status "Stopping RAG System..."
    docker-compose down
    print_status "Services stopped successfully!"
}

# Restart the services
restart() {
    print_status "Restarting RAG System..."
    stop
    start
}

# Show logs
logs() {
    echo "Showing logs (Press Ctrl+C to exit)..."
    docker-compose logs -f rag-app
}

# Show status
status() {
    print_status "Service Status:"
    docker-compose ps

    echo ""
    print_status "Health Check:"
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is healthy${NC}"
    else
        echo -e "${RED}✗ Service is not responding${NC}"
    fi
}

# Clean up (remove containers, volumes, images)
clean() {
    print_warning "This will remove all containers, volumes, and images related to RAG System."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --remove-orphans
        docker system prune -f --volumes
        print_status "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Add sample documents
add_samples() {
    print_status "Adding sample documents to the RAG system..."

    # Sample documents
    curl -X POST "http://localhost:8000/add_document" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "Docker is a platform that uses containerization technology to package applications and their dependencies into lightweight, portable containers.",
            "metadata": {"topic": "devops", "source": "docker_setup"}
        }' > /dev/null 2>&1

    curl -X POST "http://localhost:8000/add_document" \
        -H "Content-Type: application/json" \
        -d '{
            "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
            "metadata": {"topic": "web_development", "framework": "fastapi", "source": "docker_setup"}
        }' > /dev/null 2>&1

    print_status "Sample documents added successfully!"
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build      Build the Docker image (with reference checks)"
    echo "  start      Start the RAG System"
    echo "  stop       Stop the RAG System"
    echo "  restart    Restart the RAG System"
    echo "  logs       Show service logs"
    echo "  status     Show service status"
    echo "  clean      Clean up all Docker resources"
    echo "  samples    Add sample documents"
    echo "  check      Run reference and dependency checks"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 check && $0 build    # Check references then build"
    echo "  $0 build && $0 start    # Build and start the system"
    echo "  $0 logs                 # View real-time logs"
    echo "  $0 status               # Check if services are running"
}

# Main script logic
main() {
    check_docker

    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        samples)
            add_samples
            ;;
        check)
            check_references
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run the main function
main "$@"
