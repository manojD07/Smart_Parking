#!/bin/bash

# 🅿️ Smart Parking Management System - One-Click Startup
# This script starts the entire system: Backend + Frontend + Database + Sample Data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${PURPLE}🅿️ ================================================================${NC}"
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

# Check if Docker is running
check_docker() {
    print_step "Checking Docker..."
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! docker-compose --version > /dev/null 2>&1; then
        print_error "Docker Compose is not installed or not in PATH."
        exit 1
    fi
    
    print_status "Docker is ready"
}

# Clean up any existing containers
cleanup() {
    print_step "Cleaning up existing containers..."
    
    # Stop and remove containers if they exist
    docker-compose -f docker-compose.fullstack.yml down --remove-orphans > /dev/null 2>&1 || true
    
    # Clean up any dangling containers with our prefix
    docker ps -a --filter "name=smart_parking_" --format "{{.Names}}" | xargs -r docker rm -f > /dev/null 2>&1 || true
    
    print_status "Cleanup completed"
}

# Build and start all services
start_services() {
    print_step "Building and starting all services..."
    print_info "This may take a few minutes on first run..."
    
    # Build and start services in the background
    docker-compose -f docker-compose.fullstack.yml up --build -d
    
    print_status "All services are starting..."
}

# Wait for services to be healthy
wait_for_services() {
    print_step "Waiting for services to be ready..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        
        # Check database
        if docker-compose -f docker-compose.fullstack.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
            print_status "Database is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Database failed to start within expected time"
            exit 1
        fi
        
        echo -n "."
        sleep 2
    done
    
    # Wait a bit more for API to be fully ready
    print_step "Waiting for API to be ready..."
    sleep 10
    
    # Check if API is responding
    attempt=0
    while [ $attempt -lt 30 ]; do
        attempt=$((attempt + 1))
        
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_status "API is ready"
            break
        fi
        
        if [ $attempt -eq 30 ]; then
            print_warning "API health check timeout, but continuing..."
            break
        fi
        
        echo -n "."
        sleep 2
    done
    
    # Wait for frontend
    print_step "Waiting for frontend to be ready..."
    sleep 5
    
    attempt=0
    while [ $attempt -lt 20 ]; do
        attempt=$((attempt + 1))
        
        if curl -f http://localhost:4200 > /dev/null 2>&1; then
            print_status "Frontend is ready"
            break
        fi
        
        if [ $attempt -eq 20 ]; then
            print_warning "Frontend health check timeout, but continuing..."
            break
        fi
        
        echo -n "."
        sleep 3
    done
}

# Show service status
show_status() {
    print_step "Checking service status..."
    echo ""
    
    docker-compose -f docker-compose.fullstack.yml ps
    echo ""
}

# Display access information
show_access_info() {
    print_header "🎉 SMART PARKING SYSTEM IS READY!"
    
    echo -e "${GREEN}🌐 ACCESS POINTS:${NC}"
    echo -e "   ${CYAN}Frontend (Angular):${NC}     http://localhost:4200"
    echo -e "   ${CYAN}Backend API (FastAPI):${NC}  http://localhost:8000"
    echo -e "   ${CYAN}API Documentation:${NC}      http://localhost:8000/docs"
    echo -e "   ${CYAN}Celery Monitor:${NC}         http://localhost:5555"
    echo -e "   ${CYAN}Database (PostgreSQL):${NC}  localhost:5432"
    echo -e "   ${CYAN}Redis Cache:${NC}            localhost:6379"
    
    echo -e "\n${GREEN}🔐 LOGIN CREDENTIALS:${NC}"
    echo -e "   ${CYAN}Admin:${NC}  admin@smartparking.com / AdminPassword123!"
    echo -e "   ${CYAN}User:${NC}   user@smartparking.com / UserPassword123!"
    
    echo -e "\n${GREEN}📊 SAMPLE DATA:${NC}"
    echo -e "   ${CYAN}Users:${NC}         23 (including admins)"
    echo -e "   ${CYAN}Parking Lots:${NC}  7 (major Indian cities)"
    echo -e "   ${CYAN}Parking Slots:${NC} 1000+ (cars and bikes)"
    echo -e "   ${CYAN}Bookings:${NC}      Sample booking history"
    echo -e "   ${CYAN}Pricing Rules:${NC} Dynamic time-based pricing"
    
    echo -e "\n${GREEN}🛠️ MANAGEMENT:${NC}"
    echo -e "   ${CYAN}View Logs:${NC}       docker-compose -f docker-compose.fullstack.yml logs -f"
    echo -e "   ${CYAN}Stop System:${NC}     docker-compose -f docker-compose.fullstack.yml down"
    echo -e "   ${CYAN}Restart:${NC}         $0"
    
    echo -e "\n${YELLOW}📝 NOTES:${NC}"
    echo -e "   • The system automatically seeds sample data on first run"
    echo -e "   • All services are connected and ready for testing"
    echo -e "   • Check logs if any service shows as unhealthy"
    echo -e "   • Data persists in Docker volumes between restarts"
    
    print_header "Happy Testing! 🚀"
}

# Handle script arguments
handle_arguments() {
    case "${1:-}" in
        "stop")
            print_header "STOPPING SMART PARKING SYSTEM"
            docker-compose -f docker-compose.fullstack.yml down
            print_status "All services stopped"
            exit 0
            ;;
        "logs")
            print_info "Showing service logs (Press Ctrl+C to exit)"
            docker-compose -f docker-compose.fullstack.yml logs -f
            exit 0
            ;;
        "status")
            print_header "SERVICE STATUS"
            show_status
            exit 0
            ;;
        "clean")
            print_header "CLEANING UP SYSTEM"
            print_warning "This will remove all containers and data!"
            read -p "Are you sure? Type 'yes' to continue: " -r
            if [[ $REPLY == "yes" ]]; then
                docker-compose -f docker-compose.fullstack.yml down -v --remove-orphans
                docker system prune -f
                print_status "System cleaned up"
            else
                print_info "Cleanup cancelled"
            fi
            exit 0
            ;;
        "help"|"-h"|"--help")
            print_header "SMART PARKING SYSTEM MANAGEMENT"
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  (no args)  Start the complete system"
            echo "  stop       Stop all services"
            echo "  logs       Show service logs"
            echo "  status     Show service status"
            echo "  clean      Remove all containers and data"
            echo "  help       Show this help message"
            echo ""
            exit 0
            ;;
        "")
            # Default: start the system
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
    
    # Start the system
    print_header "STARTING SMART PARKING MANAGEMENT SYSTEM"
    
    # Prerequisites
    check_docker
    
    # Clean up
    cleanup
    
    # Start services
    start_services
    
    # Wait for readiness
    wait_for_services
    
    # Show status
    show_status
    
    # Show access information
    show_access_info
}

# Run main function with all arguments
main "$@"
