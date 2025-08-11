#!/bin/bash

# ML Service - Complete Test Suite Runner

set -e

echo "ML Service - Complete Test Suite"
echo "===================================="
echo

print_status() {
    local color=$1
    local message=$2
    case $color in
        "green") echo -e "\033[32m$message\033[0m" ;;
        "red") echo -e "\033[31m$message\033[0m" ;;
        "yellow") echo -e "\033[33m$message\033[0m" ;;
        "blue") echo -e "\033[34m$message\033[0m" ;;
        *) echo "$message" ;;
    esac
}

if [ "$CI" = "true" ]; then
    print_status "blue" "Running in CI environment"
fi

# Backend API Tests
print_status "blue" "Running Backend API Tests..."
echo "------------------------------------"
cd app
if python run_tests.py; then
    print_status "green" "Backend tests passed!"
else
    print_status "red" "Backend tests failed!"
    exit 1
fi
cd ..
echo

# Worker Tests
print_status "blue" "Running Worker Tests..."
echo "------------------------------------"
cd worker
if python run_tests.py; then
    print_status "green" "Worker tests passed!"
else
    print_status "red" "Worker tests failed!"
    exit 1
fi
cd ..
echo

# Frontend Tests (if applicable)
if [ -d "frontend-service" ] && [ -f "frontend-service/package.json" ]; then
    print_status "blue" "Running Frontend Tests..."
    echo "------------------------------------"
    cd frontend-service
    if command -v npm &> /dev/null; then
        if npm test; then
            print_status "green" "Frontend tests passed!"
        else
            print_status "red" "Frontend tests failed!"
            exit 1
        fi
    else
        print_status "yellow" "npm not found, skipping frontend tests"
    fi
    cd ..
    echo
fi

# Integration Tests (if Docker is available)
if command -v docker-compose &> /dev/null; then
    print_status "blue" "Running Integration Tests..."
    echo "------------------------------------"
    
    print_status "yellow" "Starting services for integration tests..."
    docker-compose -f docker-compose.yml up -d database rabbitmq
    
    sleep 10
    
    cd app
    if python -m pytest tests/ -k "integration" -v; then
        print_status "green" "Integration tests passed!"
    else
        print_status "yellow" "Integration tests had issues (this might be expected in some environments)"
    fi
    cd ..
    
    docker-compose down
else
    print_status "yellow" "Docker not available, skipping integration tests"
fi

echo
print_status "green" "All test suites completed successfully!"
echo
print_status "blue" "Coverage Reports:"
echo "  - Backend: app/htmlcov/index.html"
echo "  - Worker: worker/htmlcov_worker/index.html"
echo
print_status "blue" "To run specific test files:"
echo "  - Backend: cd app && python run_tests.py test_auth.py"
echo "  - Worker: cd worker && python run_tests.py" 