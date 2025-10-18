#!/bin/bash

# Deployment script for COVID-19 Research Analyzer
# Usage: ./deploy.sh [environment] [version]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="covid-analyzer"
REGISTRY="your-registry.com"

# Default values
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
NAMESPACE="${APP_NAME}-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Deploying to environment: $ENVIRONMENT"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check if kubectl is installed (for Kubernetes deployment)
    if ! command -v kubectl &> /dev/null; then
        log_warning "kubectl is not installed - Kubernetes deployment will not be available"
    fi
    
    # Check if required files exist
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_error "requirements.txt not found in project root"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/app.py" ]]; then
        log_error "app.py not found in project root"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build the image
    docker build \
        -f deployment/docker/Dockerfile \
        -t "${APP_NAME}:${VERSION}" \
        -t "${APP_NAME}:latest" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        .
    
    log_success "Docker image built successfully"
}

# Tag and push image to registry
push_image() {
    if [[ "$REGISTRY" != "your-registry.com" ]]; then
        log_info "Tagging and pushing image to registry..."
        
        docker tag "${APP_NAME}:${VERSION}" "${REGISTRY}/${APP_NAME}:${VERSION}"
        docker tag "${APP_NAME}:latest" "${REGISTRY}/${APP_NAME}:latest"
        
        docker push "${REGISTRY}/${APP_NAME}:${VERSION}"
        docker push "${REGISTRY}/${APP_NAME}:latest"
        
        log_success "Image pushed to registry"
    else
        log_warning "Registry not configured, skipping push"
    fi
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT/deployment/docker"
    
    # Set environment variables
    export COVID_ANALYZER_ENVIRONMENT="$ENVIRONMENT"
    export COVID_ANALYZER_VERSION="$VERSION"
    
    # Deploy
    docker-compose down --remove-orphans || true
    docker-compose up -d
    
    # Wait for health check
    log_info "Waiting for application to be healthy..."
    for i in {1..30}; do
        if curl -f http://localhost:8501/health &> /dev/null; then
            log_success "Application is healthy"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Application failed to become healthy"
            exit 1
        fi
        sleep 2
    done
    
    log_success "Docker Compose deployment completed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    if ! command -v kubectl &> /dev/null; then
        log_warning "kubectl not available, skipping Kubernetes deployment"
        return
    fi
    
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    cd "$PROJECT_ROOT/deployment/kubernetes"
    
    # Replace placeholders in manifests
    sed "s|covid-analyzer:latest|${REGISTRY}/${APP_NAME}:${VERSION}|g" deployment.yaml > deployment-${ENVIRONMENT}.yaml
    
    kubectl apply -f deployment-${ENVIRONMENT}.yaml -n "$NAMESPACE"
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/covid-analyzer -n "$NAMESPACE" --timeout=300s
    
    log_success "Kubernetes deployment completed"
    
    # Show deployment info
    kubectl get pods -n "$NAMESPACE"
    kubectl get services -n "$NAMESPACE"
}

# Run health checks
run_health_checks() {
    log_info "Running post-deployment health checks..."
    
    # Basic health check
    if curl -f http://localhost:8501/health &> /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Readiness check
    if curl -f http://localhost:8501/health/ready &> /dev/null; then
        log_success "Readiness check passed"
    else
        log_error "Readiness check failed"
        exit 1
    fi
    
    log_success "All health checks passed"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove old Docker images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting deployment of COVID-19 Research Analyzer"
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    validate_environment
    check_prerequisites
    build_image
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        push_image
        deploy_kubernetes
    else
        deploy_docker_compose
    fi
    
    run_health_checks
    cleanup
    
    log_success "Deployment completed successfully!"
    log_info "Application is available at: http://localhost:8501"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [environment] [version]"
        echo ""
        echo "Arguments:"
        echo "  environment    Target environment (development|staging|production)"
        echo "  version        Application version tag (default: latest)"
        echo ""
        echo "Examples:"
        echo "  $0 staging v1.0.0"
        echo "  $0 production latest"
        exit 0
        ;;
    *)
        main
        ;;
esac