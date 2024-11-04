#!/bin/bash

# Set script to exit on any errors.
set -e

# Define variables
PROJECT_ROOT=$(dirname "$(realpath "$0")")/..
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/deployment/docker/DockerCompose.yml"
K8S_MANIFESTS="${PROJECT_ROOT}/deployment/kubernetes/K8sManifests.yaml"
DOCKER_IMAGE_NAME="distributed-cache-system"
DOCKER_REGISTRY="registry.website.com/distributed-cache"
NAMESPACE="cache-system"

# Function to build the project
build_project() {
    echo "Building project components..."

    # Build C++ components
    echo "Building C++ components..."
    cd "${PROJECT_ROOT}/cache" && make

    # Build Java components
    echo "Building Java components..."
    cd "${PROJECT_ROOT}/distributed" && mvn clean install

    # Build Python components
    echo "Building Python components..."
    cd "${PROJECT_ROOT}/cache/persistent_cache" && python setup.py install
}

# Function to build Docker images
build_docker_images() {
    echo "Building Docker images..."
    
    # Build the Docker image
    docker build -t "${DOCKER_IMAGE_NAME}:latest" -f "${PROJECT_ROOT}/deployment/docker/Dockerfile" "${PROJECT_ROOT}"
    
    # Tag the image for the registry
    docker tag "${DOCKER_IMAGE_NAME}:latest" "${DOCKER_REGISTRY}:latest"
}

# Function to push Docker image to registry
push_docker_image() {
    echo "Pushing Docker image to registry..."
    docker push "${DOCKER_REGISTRY}:latest"
}

# Function to deploy to Kubernetes
deploy_kubernetes() {
    echo "Deploying to Kubernetes..."

    # Apply Kubernetes manifests
    kubectl apply -f "${K8S_MANIFESTS}" -n "${NAMESPACE}"
    
    echo "Deployment to Kubernetes completed."
}

# Function to run Docker Compose for local testing
deploy_docker_compose() {
    echo "Running Docker Compose for local environment..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d
}

# Function to clean up Docker Compose environment
cleanup_docker_compose() {
    echo "Cleaning up Docker Compose environment..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down
}

# Display usage information
usage() {
    echo "Usage: $0 {build|docker|push|k8s|compose|cleanup}"
    exit 1
}

# Main script logic
case "$1" in
    build)
        build_project
        ;;
    docker)
        build_docker_images
        ;;
    push)
        push_docker_image
        ;;
    k8s)
        deploy_kubernetes
        ;;
    compose)
        deploy_docker_compose
        ;;
    cleanup)
        cleanup_docker_compose
        ;;
    *)
        usage
        ;;
esac

exit 0