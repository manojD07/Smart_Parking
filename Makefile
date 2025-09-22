# Smart Parking Management System - Build System
# Makefile for building Docker images and managing the application

# Default values
REGISTRY ?= 
VERSION ?= $(shell cat VERSION 2>/dev/null || echo "1.0.0")
COMMIT_ID ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
DEV_MODE ?= false

# Image names
BACKEND_IMAGE_NAME = smart-parking-backend
FRONTEND_IMAGE_NAME = smart-parking-frontend

# Registry handling
ifeq ($(REGISTRY),)
    BACKEND_IMAGE = $(BACKEND_IMAGE_NAME):$(VERSION)
    FRONTEND_IMAGE = $(FRONTEND_IMAGE_NAME):$(VERSION)
    BACKEND_IMAGE_LATEST = $(BACKEND_IMAGE_NAME):latest
    FRONTEND_IMAGE_LATEST = $(FRONTEND_IMAGE_NAME):latest
else
    BACKEND_IMAGE = $(REGISTRY)/$(BACKEND_IMAGE_NAME):$(VERSION)
    FRONTEND_IMAGE = $(REGISTRY)/$(FRONTEND_IMAGE_NAME):$(VERSION)
    BACKEND_IMAGE_LATEST = $(REGISTRY)/$(BACKEND_IMAGE_NAME):latest
    FRONTEND_IMAGE_LATEST = $(REGISTRY)/$(FRONTEND_IMAGE_NAME):latest
endif

# Dev mode versioning
ifeq ($(DEV_MODE),true)
    BACKEND_IMAGE = $(BACKEND_IMAGE_NAME):dev-$(COMMIT_ID)
    FRONTEND_IMAGE = $(FRONTEND_IMAGE_NAME):dev-$(COMMIT_ID)
    BACKEND_IMAGE_LATEST = $(BACKEND_IMAGE_NAME):dev-latest
    FRONTEND_IMAGE_LATEST = $(FRONTEND_IMAGE_NAME):dev-latest
endif

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo -e "$(PURPLE)🅿️ Smart Parking Management System - Build System$(NC)"
	@echo -e "$(CYAN)Available targets:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(CYAN)Environment Variables:$(NC)"
	@echo "  $(YELLOW)REGISTRY$(NC)     Docker registry URL (optional, defaults to local)"
	@echo "  $(YELLOW)VERSION$(NC)      Image version (defaults to VERSION file)"
	@echo "  $(YELLOW)DEV_MODE$(NC)     Set to 'true' for dev builds with commit ID"
	@echo ""
	@echo -e "$(CYAN)Examples:$(NC)"
	@echo "  $(GREEN)make build$(NC)                    # Build all images locally"
	@echo "  $(GREEN)make build DEV_MODE=true$(NC)      # Build dev images with commit ID"
	@echo "  $(GREEN)make build REGISTRY=myregistry$(NC) # Build with custom registry"
	@echo "  $(GREEN)make docker-image$(NC)             # Build and tag images"
	@echo "  $(GREEN)make start$(NC)                    # Start the application"
	@echo "  $(GREEN)make stop$(NC)                     # Stop the application"
	@echo "  $(GREEN)make clean$(NC)                    # Clean up everything"

# Build targets
.PHONY: build
build: build-backend build-frontend ## Build all Docker images

.PHONY: build-backend
build-backend: ## Build backend Docker image
	@echo -e "$(BLUE)🔨 Building backend image: $(BACKEND_IMAGE)$(NC)"
	@docker build \
		--build-arg VERSION=$(VERSION) \
		--build-arg COMMIT_ID=$(COMMIT_ID) \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg REGISTRY=$(REGISTRY) \
		-t $(BACKEND_IMAGE) \
		-t $(BACKEND_IMAGE_LATEST) \
		./backend
	@echo -e "$(GREEN)✅ Backend image built successfully$(NC)"

.PHONY: build-frontend
build-frontend: ## Build frontend Docker image
	@echo -e "$(BLUE)🔨 Building frontend image: $(FRONTEND_IMAGE)$(NC)"
	@docker build \
		--build-arg VERSION=$(VERSION) \
		--build-arg COMMIT_ID=$(COMMIT_ID) \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg REGISTRY=$(REGISTRY) \
		-t $(FRONTEND_IMAGE) \
		-t $(FRONTEND_IMAGE_LATEST) \
		./frontend
	@echo -e "$(GREEN)✅ Frontend image built successfully$(NC)"

# Docker image management
.PHONY: docker-image
docker-image: build ## Build and tag Docker images (alias for build)
	@echo -e "$(GREEN)✅ All images built and tagged$(NC)"

.PHONY: push
push: ## Push images to registry
	@echo -e "$(BLUE)📤 Pushing images to registry...$(NC)"
	@docker push $(BACKEND_IMAGE)
	@docker push $(FRONTEND_IMAGE)
	@echo -e "$(GREEN)✅ Images pushed successfully$(NC)"

.PHONY: pull
pull: ## Pull images from registry
	@echo -e "$(BLUE)📥 Pulling images from registry...$(NC)"
	@docker pull $(BACKEND_IMAGE)
	@docker pull $(FRONTEND_IMAGE)
	@echo -e "$(GREEN)✅ Images pulled successfully$(NC)"

# Application management
.PHONY: start
start: ## Start the application using docker-compose
	@echo -e "$(BLUE)🚀 Starting Smart Parking System...$(NC)"
	@./smart-parking --start

.PHONY: stop
stop: ## Stop the application
	@echo -e "$(YELLOW)🛑 Stopping Smart Parking System...$(NC)"
	@./smart-parking --stop

.PHONY: restart
restart: stop start ## Restart the application

.PHONY: status
status: ## Show application status
	@./smart-parking --status

.PHONY: logs
logs: ## Show application logs
	@./smart-parking --logs

.PHONY: clean
clean: ## Clean up containers, images, and volumes
	@echo -e "$(RED)🧹 Cleaning up Smart Parking System...$(NC)"
	@./smart-parking --cleanup

# Development targets
.PHONY: dev-build
dev-build: ## Build development images with commit ID
	@echo -e "$(BLUE)🔨 Building development images...$(NC)"
	@$(MAKE) build DEV_MODE=true
	@echo -e "$(GREEN)✅ Development images built$(NC)"

.PHONY: dev-start
dev-start: dev-build start ## Build dev images and start application

# Utility targets
.PHONY: version
version: ## Show current version information
	@echo -e "$(CYAN)Version Information:$(NC)"
	@echo "  Version: $(VERSION)"
	@echo "  Commit ID: $(COMMIT_ID)"
	@echo "  Dev Mode: $(DEV_MODE)"
	@echo "  Registry: $(if $(REGISTRY),$(REGISTRY),local)"
	@echo "  Backend Image: $(BACKEND_IMAGE)"
	@echo "  Frontend Image: $(FRONTEND_IMAGE)"

.PHONY: images
images: ## List built images
	@echo -e "$(CYAN)Smart Parking Images:$(NC)"
	@docker images | grep smart-parking || echo "No smart-parking images found"

.PHONY: clean-images
clean-images: ## Remove all smart-parking images
	@echo -e "$(YELLOW)🗑️ Removing smart-parking images...$(NC)"
	@docker images -q smart-parking* | xargs -r docker rmi -f
	@echo -e "$(GREEN)✅ Images removed$(NC)"

.PHONY: clean-all
clean-all: clean clean-images ## Clean everything including images

# Docker Compose targets
.PHONY: up
up: start ## Start services (alias for start)

.PHONY: down
down: stop ## Stop services (alias for stop)

.PHONY: ps
ps: status ## Show service status (alias for status)

# Build info
.PHONY: info
info: version images ## Show build and image information

# Validate targets
.PHONY: validate
validate: ## Validate Docker setup
	@echo -e "$(BLUE)🔍 Validating Docker setup...$(NC)"
	@docker --version > /dev/null || (echo -e "$(RED)❌ Docker not found$(NC)" && exit 1)
	@docker-compose --version > /dev/null || (echo -e "$(RED)❌ Docker Compose not found$(NC)" && exit 1)
	@test -f VERSION || (echo -e "$(RED)❌ VERSION file not found$(NC)" && exit 1)
	@echo -e "$(GREEN)✅ Docker setup is valid$(NC)"

# Show current configuration
.PHONY: config
config: ## Show current build configuration
	@echo -e "$(PURPLE)🅿️ Smart Parking Build Configuration$(NC)"
	@echo -e "$(CYAN)=====================================$(NC)"
	@echo "Registry: $(if $(REGISTRY),$(REGISTRY),local)"
	@echo "Version: $(VERSION)"
	@echo "Commit ID: $(COMMIT_ID)"
	@echo "Dev Mode: $(DEV_MODE)"
	@echo ""
	@echo -e "$(CYAN)Images:$(NC)"
	@echo "Backend: $(BACKEND_IMAGE)"
	@echo "Frontend: $(FRONTEND_IMAGE)"
	@echo ""
	@echo -e "$(CYAN)Available Commands:$(NC)"
	@echo "  make build          - Build all images"
	@echo "  make start          - Start application"
	@echo "  make stop           - Stop application"
	@echo "  make clean          - Clean up everything"
	@echo "  make help           - Show this help"
