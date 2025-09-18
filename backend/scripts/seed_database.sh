#!/bin/bash

# Smart Parking Management System - Database Seeding Script
# This script provides easy commands to seed and manage sample data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if database is ready
check_database() {
    print_info "Checking database connection..."
    
    if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        print_status "Database is ready"
    else
        print_error "Database is not ready. Please ensure Docker services are running."
        print_info "Run: docker-compose up -d"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    if docker-compose exec -T api alembic upgrade head; then
        print_status "Database migrations completed"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Seed with Python script
seed_with_python() {
    print_info "Seeding database with Python script..."
    
    if docker-compose exec -T api python scripts/seed_comprehensive_data.py; then
        print_status "Python seeding completed successfully"
    else
        print_error "Python seeding failed"
        exit 1
    fi
}

# Seed with SQL script
seed_with_sql() {
    print_info "Seeding database with SQL script..."
    
    if docker-compose exec -T db psql -U postgres -d smart_parking -f /app/scripts/seed_data.sql; then
        print_status "SQL seeding completed successfully"
    else
        print_error "SQL seeding failed"
        exit 1
    fi
}

# Create database dump
create_dump() {
    print_info "Creating database dump..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    DUMP_FILE="smart_parking_dump_${TIMESTAMP}.sql"
    
    if docker-compose exec -T db pg_dump -U postgres -d smart_parking > "database_dumps/${DUMP_FILE}"; then
        print_status "Database dump created: database_dumps/${DUMP_FILE}"
    else
        print_error "Failed to create database dump"
        exit 1
    fi
}

# Show database statistics
show_stats() {
    print_info "Getting database statistics..."
    
    docker-compose exec -T db psql -U postgres -d smart_parking -c "
    SELECT 
        'Users' as table_name, COUNT(*) as record_count FROM users
    UNION ALL
    SELECT 
        'Parking Lots' as table_name, COUNT(*) as record_count FROM parking_lots
    UNION ALL
    SELECT 
        'Parking Slots' as table_name, COUNT(*) as record_count FROM parking_slots
    UNION ALL
    SELECT 
        'Pricing Rules' as table_name, COUNT(*) as record_count FROM pricing_rules
    UNION ALL
    SELECT 
        'Bookings' as table_name, COUNT(*) as record_count FROM bookings;
    "
}

# Reset database (dangerous!)
reset_database() {
    print_warning "This will DELETE ALL DATA and recreate the database!"
    read -p "Are you sure? Type 'yes' to continue: " -r
    
    if [[ $REPLY == "yes" ]]; then
        print_info "Resetting database..."
        
        # Drop and recreate database
        docker-compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS smart_parking;"
        docker-compose exec -T db psql -U postgres -c "CREATE DATABASE smart_parking;"
        
        # Run migrations
        run_migrations
        
        print_status "Database reset completed"
    else
        print_info "Database reset cancelled"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "🗄️ Smart Parking Database Management"
    echo "=================================="
    echo ""
    echo "1. 🌱 Seed Database (Python - Comprehensive)"
    echo "2. 📄 Seed Database (SQL - Quick)"
    echo "3. 🗄️ Create Database Dump"
    echo "4. 📊 Show Database Statistics"
    echo "5. 🔄 Run Migrations Only"
    echo "6. 🧹 Reset Database (DANGER!)"
    echo "7. ❌ Exit"
    echo ""
}

# Main execution
main() {
    # Check prerequisites
    check_docker
    check_database
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Choose an option (1-7): " choice
            
            case $choice in
                1)
                    run_migrations
                    seed_with_python
                    ;;
                2)
                    run_migrations
                    seed_with_sql
                    ;;
                3)
                    mkdir -p database_dumps
                    create_dump
                    ;;
                4)
                    show_stats
                    ;;
                5)
                    run_migrations
                    ;;
                6)
                    reset_database
                    ;;
                7)
                    print_info "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option. Please choose 1-7."
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case $1 in
            "seed-python")
                run_migrations
                seed_with_python
                ;;
            "seed-sql")
                run_migrations
                seed_with_sql
                ;;
            "dump")
                mkdir -p database_dumps
                create_dump
                ;;
            "stats")
                show_stats
                ;;
            "migrate")
                run_migrations
                ;;
            "reset")
                reset_database
                ;;
            *)
                echo "Usage: $0 [seed-python|seed-sql|dump|stats|migrate|reset]"
                echo ""
                echo "Commands:"
                echo "  seed-python  - Seed with comprehensive Python script"
                echo "  seed-sql     - Seed with quick SQL script"
                echo "  dump         - Create database dump"
                echo "  stats        - Show database statistics"
                echo "  migrate      - Run migrations only"
                echo "  reset        - Reset database (DANGER!)"
                echo ""
                echo "Run without arguments for interactive mode."
                ;;
        esac
    fi
}

# Create database_dumps directory
mkdir -p database_dumps

# Run main function
main "$@"
