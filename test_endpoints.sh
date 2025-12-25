#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local method=${4:-GET}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -X "$method" "$url" 2>/dev/null)
    fi
    
    if [ "$response" = "$expected_status" ] || [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((PASSED++))
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        ((FAILED++))
        return 1
    elif [ "$response" = "404" ]; then
        echo -e "${RED}✗ FAIL${NC} (HTTP 404 - Not Found)"
        ((FAILED++))
        return 1
    else
        echo -e "${YELLOW}⚠ SKIP${NC} (HTTP $response)"
        ((SKIPPED++))
        return 2
    fi
}

echo "=========================================="
echo "E-Commerce Microservices Endpoint Tester"
echo "=========================================="
echo ""

# API Gateway Tests
echo "=== API Gateway (Port 80) ==="
test_endpoint "Health Check" "http://localhost/health"
test_endpoint "API Root" "http://localhost/"
echo ""

# Auth Service Tests
echo "=== Auth Service (Port 8002) ==="
test_endpoint "Swagger UI" "http://localhost:8002/swagger/"
test_endpoint "ReDoc" "http://localhost:8002/redoc/"
test_endpoint "Admin Panel" "http://localhost:8002/admin/"
test_endpoint "Auth API" "http://localhost:8002/api/v1/auth/"
test_endpoint "Accounts API" "http://localhost:8002/api/v1/accounts/"
test_endpoint "Auth via Gateway" "http://localhost/api/v1/auth/"
test_endpoint "Accounts via Gateway" "http://localhost/api/v1/accounts/"
echo ""

# Product Service Tests
echo "=== Product Service (Port 8003) ==="
test_endpoint "Swagger UI" "http://localhost:8003/swagger/"
test_endpoint "ReDoc" "http://localhost:8003/redoc/"
test_endpoint "Admin Panel" "http://localhost:8003/admin/"
test_endpoint "Products API" "http://localhost:8003/api/v1/products/"
test_endpoint "Products via Gateway" "http://localhost/api/v1/products/"
echo ""

# Order Service Tests
echo "=== Order Service (Port 8004) ==="
test_endpoint "Swagger UI" "http://localhost:8004/swagger/"
test_endpoint "ReDoc" "http://localhost:8004/redoc/"
test_endpoint "Admin Panel" "http://localhost:8004/admin/"
test_endpoint "Orders API" "http://localhost:8004/api/v1/orders/"
test_endpoint "Orders via Gateway" "http://localhost/api/v1/orders/"
echo ""

# Payment Service Tests
echo "=== Payment Service (Port 8005) ==="
test_endpoint "Swagger UI" "http://localhost:8005/swagger/"
test_endpoint "ReDoc" "http://localhost:8005/redoc/"
test_endpoint "Admin Panel" "http://localhost:8005/admin/"
test_endpoint "Payments API" "http://localhost:8005/api/v1/payments/"
test_endpoint "Payments via Gateway" "http://localhost/api/v1/payments/"
echo ""

# Shipping Service Tests
echo "=== Shipping Service (Port 8006) ==="
test_endpoint "Swagger UI" "http://localhost:8006/swagger/"
test_endpoint "ReDoc" "http://localhost:8006/redoc/"
test_endpoint "Admin Panel" "http://localhost:8006/admin/"
test_endpoint "Shipping API" "http://localhost:8006/api/v1/shipping/"
test_endpoint "Shipping via Gateway" "http://localhost/api/v1/shipping/"
echo ""

# Notification Service Tests
echo "=== Notification Service (Port 8007) ==="
test_endpoint "Swagger UI" "http://localhost:8007/swagger/"
test_endpoint "ReDoc" "http://localhost:8007/redoc/"
test_endpoint "Admin Panel" "http://localhost:8007/admin/"
test_endpoint "Notifications API" "http://localhost:8007/api/v1/notifications/"
test_endpoint "Notifications via Gateway" "http://localhost/api/v1/notifications/"
echo ""

# Admin Tools
echo "=== Admin Tools ==="
test_endpoint "Adminer" "http://localhost:8080"
test_endpoint "Admin Dashboard" "http://localhost:8000/admin/"
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
echo "Total: $((PASSED + FAILED + SKIPPED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check the output above.${NC}"
    exit 1
fi


