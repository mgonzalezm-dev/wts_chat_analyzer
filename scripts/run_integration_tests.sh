#!/bin/bash

# Integration Test Runner for WhatsApp Conversation Analyzer
# This script runs all tests across backend, frontend, and E2E

set -e  # Exit on error

echo "🧪 WhatsApp Conversation Analyzer - Integration Test Suite"
echo "========================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
BACKEND_UNIT_PASSED=false
BACKEND_INTEGRATION_PASSED=false
FRONTEND_UNIT_PASSED=false
E2E_PASSED=false

# Function to print test section
print_section() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to check if services are running
check_services() {
    print_section "Checking Required Services"
    
    # Check PostgreSQL
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${RED}✗ PostgreSQL is not running${NC}"
        echo "Please start PostgreSQL before running tests"
        exit 1
    fi
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${RED}✗ Redis is not running${NC}"
        echo "Please start Redis before running tests"
        exit 1
    fi
}

# Backend Unit Tests
run_backend_unit_tests() {
    print_section "Running Backend Unit Tests"
    
    cd backend
    
    if python run_tests.py --type unit --coverage; then
        echo -e "${GREEN}✓ Backend unit tests passed${NC}"
        BACKEND_UNIT_PASSED=true
    else
        echo -e "${RED}✗ Backend unit tests failed${NC}"
    fi
    
    cd ..
}

# Backend Integration Tests
run_backend_integration_tests() {
    print_section "Running Backend Integration Tests"
    
    cd backend
    
    if python run_tests.py --type integration; then
        echo -e "${GREEN}✓ Backend integration tests passed${NC}"
        BACKEND_INTEGRATION_PASSED=true
    else
        echo -e "${RED}✗ Backend integration tests failed${NC}"
    fi
    
    cd ..
}

# Frontend Unit Tests
run_frontend_unit_tests() {
    print_section "Running Frontend Unit Tests"
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    if npm run test -- --run; then
        echo -e "${GREEN}✓ Frontend unit tests passed${NC}"
        FRONTEND_UNIT_PASSED=true
    else
        echo -e "${RED}✗ Frontend unit tests failed${NC}"
    fi
    
    cd ..
}

# Start services for E2E tests
start_services() {
    print_section "Starting Services for E2E Tests"
    
    # Start backend
    cd backend
    echo "Starting backend server..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Start frontend
    cd frontend
    echo "Starting frontend dev server..."
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running${NC}"
    else
        echo -e "${RED}✗ Backend failed to start${NC}"
        cat backend.log
        cleanup_services
        exit 1
    fi
    
    if curl -f http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running${NC}"
    else
        echo -e "${RED}✗ Frontend failed to start${NC}"
        cat frontend.log
        cleanup_services
        exit 1
    fi
}

# Cleanup services
cleanup_services() {
    echo "Cleaning up services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Clean up any orphaned processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    # Remove log files
    rm -f backend.log frontend.log
}

# E2E Tests
run_e2e_tests() {
    print_section "Running E2E Tests with Cypress"
    
    cd frontend
    
    if npm run e2e; then
        echo -e "${GREEN}✓ E2E tests passed${NC}"
        E2E_PASSED=true
    else
        echo -e "${RED}✗ E2E tests failed${NC}"
    fi
    
    cd ..
}

# Performance Tests
run_performance_tests() {
    print_section "Running Performance Tests"
    
    echo "Testing API response times..."
    
    # Test login endpoint
    LOGIN_TIME=$(curl -o /dev/null -s -w '%{time_total}' -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"test@example.com","password":"testpassword"}')
    
    echo "Login endpoint: ${LOGIN_TIME}s"
    
    # Test conversation list endpoint (requires auth)
    # This is a simplified test - in real scenario, you'd use a valid token
    LIST_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/api/v1/conversations)
    
    echo "Conversation list endpoint: ${LIST_TIME}s"
    
    # Check if response times meet requirements
    if (( $(echo "$LOGIN_TIME < 0.5" | bc -l) )); then
        echo -e "${GREEN}✓ Login response time is acceptable${NC}"
    else
        echo -e "${YELLOW}⚠ Login response time is slow (${LOGIN_TIME}s > 0.5s)${NC}"
    fi
}

# Generate test report
generate_report() {
    print_section "Test Summary Report"
    
    TOTAL_PASSED=0
    TOTAL_TESTS=4
    
    echo "Test Results:"
    echo "============="
    
    if [ "$BACKEND_UNIT_PASSED" = true ]; then
        echo -e "${GREEN}✓ Backend Unit Tests: PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}✗ Backend Unit Tests: FAILED${NC}"
    fi
    
    if [ "$BACKEND_INTEGRATION_PASSED" = true ]; then
        echo -e "${GREEN}✓ Backend Integration Tests: PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}✗ Backend Integration Tests: FAILED${NC}"
    fi
    
    if [ "$FRONTEND_UNIT_PASSED" = true ]; then
        echo -e "${GREEN}✓ Frontend Unit Tests: PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}✗ Frontend Unit Tests: FAILED${NC}"
    fi
    
    if [ "$E2E_PASSED" = true ]; then
        echo -e "${GREEN}✓ E2E Tests: PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}✗ E2E Tests: FAILED${NC}"
    fi
    
    echo ""
    echo "Overall: $TOTAL_PASSED/$TOTAL_TESTS tests passed"
    
    # Generate detailed report file
    REPORT_FILE="test_report_$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "WhatsApp Conversation Analyzer - Test Report"
        echo "Generated: $(date)"
        echo ""
        echo "Test Results Summary:"
        echo "===================="
        echo "Backend Unit Tests: $([ "$BACKEND_UNIT_PASSED" = true ] && echo "PASSED" || echo "FAILED")"
        echo "Backend Integration Tests: $([ "$BACKEND_INTEGRATION_PASSED" = true ] && echo "PASSED" || echo "FAILED")"
        echo "Frontend Unit Tests: $([ "$FRONTEND_UNIT_PASSED" = true ] && echo "PASSED" || echo "FAILED")"
        echo "E2E Tests: $([ "$E2E_PASSED" = true ] && echo "PASSED" || echo "FAILED")"
        echo ""
        echo "Coverage Reports:"
        echo "================"
        echo "Backend coverage report: backend/htmlcov/index.html"
        echo "Frontend coverage report: frontend/coverage/index.html"
        echo ""
        echo "Performance Metrics:"
        echo "==================="
        echo "Login endpoint response time: ${LOGIN_TIME}s"
        echo "Conversation list response time: ${LIST_TIME}s"
    } > "$REPORT_FILE"
    
    echo ""
    echo "Detailed report saved to: $REPORT_FILE"
    
    # Return appropriate exit code
    if [ $TOTAL_PASSED -eq $TOTAL_TESTS ]; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    # Trap to ensure cleanup on exit
    trap cleanup_services EXIT
    
    # Check if running in CI mode
    CI_MODE=${CI:-false}
    
    if [ "$CI_MODE" = true ]; then
        echo "Running in CI mode"
    fi
    
    # Run tests
    check_services
    run_backend_unit_tests
    run_backend_integration_tests
    run_frontend_unit_tests
    
    # Only run E2E tests if not in CI mode or if explicitly requested
    if [ "$CI_MODE" != true ] || [ "$RUN_E2E" = true ]; then
        start_services
        run_e2e_tests
        run_performance_tests
    fi
    
    # Generate report
    generate_report
}

# Run main function
main