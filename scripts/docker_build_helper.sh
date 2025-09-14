#!/bin/bash

# Docker Hub Rate Limit and Build Strategy Script
# This script helps manage Docker Hub rate limits and provides alternative build strategies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "    Docker Build Strategy Helper"
    echo "========================================"
    echo -e "${NC}"
}

check_docker_hub_rate_limit() {
    echo -e "${YELLOW}[INFO]${NC} Checking Docker Hub rate limit status..."

    # Try to pull a small image to test rate limits
    if docker pull hello-world:latest > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Hub access is working${NC}"
        return 0
    else
        echo -e "${RED}❌ Docker Hub rate limit detected or connection issue${NC}"
        return 1
    fi
}

suggest_alternatives() {
    echo -e "${YELLOW}[INFO]${NC} Docker Hub rate limit detected. Here are your options:"
    echo ""
    echo "1. 🕐 Wait and retry (rate limit resets every 6 hours)"
    echo "2. 🔑 Login to Docker Hub (increases rate limit)"
    echo "3. 🏠 Use local Python installation for development"
    echo "4. 🐳 Use alternative base images"
    echo ""
}

option_wait() {
    echo -e "${YELLOW}[OPTION 1]${NC} Waiting for rate limit reset..."
    echo "Rate limits reset every 6 hours. You can:"
    echo "- Wait a few hours and try again"
    echo "- Use the development server instead: python -m uvicorn app.main:app --reload"
}

option_login() {
    echo -e "${YELLOW}[OPTION 2]${NC} Docker Hub Login"
    echo "Logging into Docker Hub increases your rate limit significantly."
    echo ""
    read -p "Do you have a Docker Hub account? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Please run: docker login"
        echo "Then try building again."
    else
        echo "You can create a free account at: https://hub.docker.com"
        echo "Free accounts get 200 pulls per 6 hours vs 100 for anonymous."
    fi
}

option_development() {
    echo -e "${YELLOW}[OPTION 3]${NC} Development Server (No Docker)"
    echo "You can run the RAG system directly without Docker:"
    echo ""
    echo "# Install dependencies"
    echo "pip install -r requirements.txt"
    echo ""
    echo "# Run the server"
    echo "python -m uvicorn app.main:app --reload --port 8000"
    echo ""
    echo "This bypasses Docker entirely and uses your local Python environment."
}

option_alternative_base() {
    echo -e "${YELLOW}[OPTION 4]${NC} Alternative Base Images"
    echo "We can modify the Dockerfile to use alternative registries:"
    echo ""
    echo "1. Use GitHub Container Registry"
    echo "2. Use Red Hat Quay.io"
    echo "3. Use a cached local image"
    echo ""

    read -p "Would you like to try an alternative base image? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_alternative_dockerfile
    fi
}

create_alternative_dockerfile() {
    echo -e "${GREEN}[INFO]${NC} Creating alternative Dockerfile..."

    # Backup original
    if [ -f "Dockerfile" ]; then
        cp Dockerfile Dockerfile.original
        echo "✅ Original Dockerfile backed up as Dockerfile.original"
    fi

    # Create alternative Dockerfile using a different registry
    cat > Dockerfile.alternative << 'EOF'
# Alternative Dockerfile using GitHub Container Registry
FROM ghcr.io/python/cpython:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

RUN mkdir -p /app/chroma_db /app/data

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    echo "✅ Alternative Dockerfile created as Dockerfile.alternative"
    echo ""
    echo "To use it:"
    echo "1. mv Dockerfile.alternative Dockerfile"
    echo "2. ./docker/manage.sh build"
}

run_reference_check() {
    echo -e "${GREEN}[INFO]${NC} Running reference checks..."

    if [ -f "scripts/check_references.py" ]; then
        if command -v python3 > /dev/null 2>&1; then
            python3 scripts/check_references.py
            return $?
        else
            echo -e "${YELLOW}[WARNING]${NC} Python3 not found. Skipping reference checks."
            return 0
        fi
    else
        echo -e "${YELLOW}[WARNING]${NC} Reference checker not found."
        return 0
    fi
}

show_build_options() {
    echo -e "${BLUE}[BUILD OPTIONS]${NC}"
    echo "1. 🔄 Retry Docker build"
    echo "2. 🔑 Login to Docker Hub first"
    echo "3. 🏠 Run without Docker"
    echo "4. 🐳 Use alternative base image"
    echo "5. ℹ️  Show detailed help"
    echo "6. ❌ Exit"
    echo ""
}

main_menu() {
    while true; do
        show_build_options
        read -p "Choose an option (1-6): " choice

        case $choice in
            1)
                echo -e "${GREEN}[INFO]${NC} Attempting Docker build..."
                if check_docker_hub_rate_limit; then
                    ./docker/manage.sh build
                    break
                else
                    suggest_alternatives
                fi
                ;;
            2)
                option_login
                ;;
            3)
                option_development
                break
                ;;
            4)
                option_alternative_base
                ;;
            5)
                show_detailed_help
                ;;
            6)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo -e "${RED}[ERROR]${NC} Invalid option. Please choose 1-6."
                ;;
        esac
        echo ""
    done
}

show_detailed_help() {
    echo -e "${BLUE}[DETAILED HELP]${NC}"
    echo ""
    echo "🐳 Docker Hub Rate Limits:"
    echo "  - Anonymous: 100 pulls per 6 hours"
    echo "  - Free account: 200 pulls per 6 hours"
    echo "  - Pro account: 5000 pulls per day"
    echo ""
    echo "🔧 Solutions:"
    echo "  1. Wait for rate limit reset (every 6 hours)"
    echo "  2. Create free Docker Hub account and login"
    echo "  3. Use development mode without Docker"
    echo "  4. Use alternative container registries"
    echo ""
    echo "🏃 Quick Development Setup:"
    echo "  pip install -r requirements.txt"
    echo "  python -m uvicorn app.main:app --reload"
    echo ""
    echo "🌐 Alternative Registries:"
    echo "  - GitHub Container Registry (ghcr.io)"
    echo "  - Red Hat Quay (quay.io)"
    echo "  - Amazon ECR Public"
    echo ""
}

main() {
    print_header

    echo -e "${GREEN}[INFO]${NC} Checking system readiness..."

    # Run reference checks first
    if ! run_reference_check; then
        echo -e "${RED}[ERROR]${NC} Reference checks failed. Please fix issues first."
        exit 1
    fi

    echo -e "${GREEN}✅ Reference checks passed${NC}"
    echo ""

    # Check Docker Hub access
    if check_docker_hub_rate_limit; then
        echo -e "${GREEN}[INFO]${NC} Docker Hub is accessible. You can build normally."
        echo ""
        read -p "Would you like to build now? (Y/n): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Nn]$ ]]; then
            main_menu
        else
            ./docker/manage.sh build
        fi
    else
        echo -e "${YELLOW}[INFO]${NC} Docker Hub rate limit detected or connection issue."
        main_menu
    fi
}

# Run main function
main "$@"
