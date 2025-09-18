#!/bin/bash

# 🅿️ Smart Parking Management System - Development Mode
# This script starts backend services with Docker and frontend with ng serve

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${PURPLE}🛠️ ================================================================${NC}"
    echo -e "${PURPLE}   $1${NC}"
    echo -e "${PURPLE}================================================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${CYAN}🔄 $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check Docker
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check Node.js and npm
    if ! node --version > /dev/null 2>&1; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Check Angular CLI
    if ! ng version > /dev/null 2>&1; then
        print_warning "Angular CLI not found. Installing globally..."
        npm install -g @angular/cli
    fi
    
    print_status "Prerequisites check passed"
}

# Install frontend dependencies
install_frontend_deps() {
    print_step "Installing frontend dependencies..."
    
    cd frontend
    
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
        print_info "Installing npm packages..."
        npm install
    else
        print_info "Dependencies are up to date"
    fi
    
    cd ..
    print_status "Frontend dependencies ready"
}

# Start backend services
start_backend() {
    print_step "Starting backend services..."
    
    # Clean up any existing containers
    docker-compose -f docker-compose.dev.yml down --remove-orphans > /dev/null 2>&1 || true
    
    # Start backend services
    docker-compose -f docker-compose.dev.yml up --build -d
    
    print_status "Backend services are starting..."
    
    # Wait for backend to be ready
    print_step "Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_status "Backend is ready"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Backend failed to start within expected time"
            print_info "Check logs with: docker-compose -f docker-compose.dev.yml logs"
            exit 1
        fi
        
        echo -n "."
        sleep 2
    done
}

# Start frontend
start_frontend() {
    print_step "Starting frontend development server..."
    
    cd frontend
    
    print_info "Frontend will be available at: http://localhost:4200"
    print_info "Press Ctrl+C to stop all services"
    
    # Start Angular dev server
    ng serve --host 0.0.0.0 --port 4200 --open
}

# Handle cleanup on exit
cleanup() {
    print_step "Stopping services..."
    
    # Kill Angular dev server if running
    pkill -f "ng serve" > /dev/null 2>&1 || true
    
    # Stop Docker services
    docker-compose -f docker-compose.dev.yml down > /dev/null 2>&1 || true
    
    print_status "All services stopped"
}

# Show development info
show_dev_info() {
    print_header "🛠️ DEVELOPMENT MODE STARTING"
    
    echo -e "${GREEN}📋 WHAT THIS DOES:${NC}"
    echo -e "   • Starts backend services with Docker (API, DB, Redis, Celery)"
    echo -e "   • Seeds comprehensive sample data automatically"
    echo -e "   • Starts frontend with ng serve for hot reload"
    echo -e "   • Enables development features and debugging"
    
    echo -e "\n${GREEN}🌐 DEVELOPMENT URLS:${NC}"
    echo -e "   ${CYAN}Frontend (ng serve):${NC}     http://localhost:4200"
    echo -e "   ${CYAN}Backend API:${NC}             http://localhost:8000"
    echo -e "   ${CYAN}API Documentation:${NC}      http://localhost:8000/docs"
    echo -e "   ${CYAN}Celery Monitor:${NC}         http://localhost:5555"
    
    echo -e "\n${GREEN}🔐 LOGIN CREDENTIALS:${NC}"
    echo -e "   ${CYAN}Admin:${NC}  admin@smartparking.com / AdminPassword123!"
    echo -e "   ${CYAN}User:${NC}   user@smartparking.com / UserPassword123!"
    
    echo -e "\n${YELLOW}📝 DEVELOPMENT NOTES:${NC}"
    echo -e "   • Frontend has hot reload enabled"
    echo -e "   • Backend has auto-reload on file changes"
    echo -e "   • Database data persists between restarts"
    echo -e "   • Press Ctrl+C to stop all services"
    
    echo ""
}

# Handle script arguments
handle_arguments() {
    case "${1:-}" in
        "stop")
            print_header "STOPPING DEVELOPMENT SERVICES"
            cleanup
            exit 0
            ;;
        "logs")
            print_info "Showing backend service logs (Press Ctrl+C to exit)"
            docker-compose -f docker-compose.dev.yml logs -f
            exit 0
            ;;
        "backend-only")
            print_header "STARTING BACKEND SERVICES ONLY"
            check_prerequisites
            start_backend
            print_info "Backend services are running. Frontend can be started separately with 'ng serve'"
            docker-compose -f docker-compose.dev.yml logs -f
            exit 0
            ;;
        "help"|"-h"|"--help")
            print_header "DEVELOPMENT MODE HELP"
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  (no args)     Start full development environment"
            echo "  backend-only  Start only backend services"
            echo "  stop          Stop all services"
            echo "  logs          Show backend service logs"
            echo "  help          Show this help message"
            echo ""
            exit 0
            ;;
        "")
            # Default: start full development environment
            ;;
        *)
            print_error "Unknown command: $1"
            print_info "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    # Handle command line arguments
    handle_arguments "$@"
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Show development info
    show_dev_info
    
    # Start development environment
    check_prerequisites
    install_frontend_deps
    start_backend
    start_frontend
}

# Run main function with all arguments
main "$@"
