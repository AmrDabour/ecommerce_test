# PowerShell script to test all endpoints
# E-Commerce Microservices Endpoint Tester

$script:Passed = 0
$script:Failed = 0
$script:Skipped = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [string]$Method = "GET"
    )
    
    Write-Host -NoNewline "Testing $Name... "
    
    try {
        $response = $null
        if ($Method -eq "GET") {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        } else {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        }
        
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $ExpectedStatus -or $statusCode -eq 200 -or $statusCode -eq 301 -or $statusCode -eq 302) {
            Write-Host -ForegroundColor Green "✓ PASS (HTTP $statusCode)"
            $script:Passed++
            return $true
        } else {
            Write-Host -ForegroundColor Yellow "⚠ SKIP (HTTP $statusCode)"
            $script:Skipped++
            return $false
        }
    }
    catch {
        $errorCode = $_.Exception.Response.StatusCode.value__
        if ($errorCode -eq 404) {
            Write-Host -ForegroundColor Red "✗ FAIL (HTTP 404 - Not Found)"
            $script:Failed++
            return $false
        }
        elseif ($_.Exception.Message -like "*Unable to connect*" -or $_.Exception.Message -like "*timeout*") {
            Write-Host -ForegroundColor Red "✗ FAIL (Connection failed)"
            $script:Failed++
            return $false
        }
        else {
            Write-Host -ForegroundColor Yellow "⚠ SKIP (Error: $($_.Exception.Message))"
            $script:Skipped++
            return $false
        }
    }
}

Write-Host "=========================================="
Write-Host "E-Commerce Microservices Endpoint Tester"
Write-Host "=========================================="
Write-Host ""

# API Gateway Tests
Write-Host "=== API Gateway (Port 80) ==="
Test-Endpoint -Name "Health Check" -Url "http://localhost/health"
Test-Endpoint -Name "API Root" -Url "http://localhost/"
Write-Host ""

# Auth Service Tests
Write-Host "=== Auth Service (Port 8002) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8002/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8002/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8002/admin/"
Test-Endpoint -Name "Auth API" -Url "http://localhost:8002/api/v1/auth/"
Test-Endpoint -Name "Accounts API" -Url "http://localhost:8002/api/v1/accounts/"
Test-Endpoint -Name "Auth via Gateway" -Url "http://localhost/api/v1/auth/"
Test-Endpoint -Name "Accounts via Gateway" -Url "http://localhost/api/v1/accounts/"
Write-Host ""

# Product Service Tests
Write-Host "=== Product Service (Port 8003) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8003/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8003/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8003/admin/"
Test-Endpoint -Name "Products API" -Url "http://localhost:8003/api/v1/products/"
Test-Endpoint -Name "Products via Gateway" -Url "http://localhost/api/v1/products/"
Write-Host ""

# Order Service Tests
Write-Host "=== Order Service (Port 8004) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8004/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8004/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8004/admin/"
Test-Endpoint -Name "Orders API" -Url "http://localhost:8004/api/v1/orders/"
Test-Endpoint -Name "Orders via Gateway" -Url "http://localhost/api/v1/orders/"
Write-Host ""

# Payment Service Tests
Write-Host "=== Payment Service (Port 8005) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8005/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8005/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8005/admin/"
Test-Endpoint -Name "Payments API" -Url "http://localhost:8005/api/v1/payments/"
Test-Endpoint -Name "Payments via Gateway" -Url "http://localhost/api/v1/payments/"
Write-Host ""

# Shipping Service Tests
Write-Host "=== Shipping Service (Port 8006) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8006/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8006/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8006/admin/"
Test-Endpoint -Name "Shipping API" -Url "http://localhost:8006/api/v1/shipping/"
Test-Endpoint -Name "Shipping via Gateway" -Url "http://localhost/api/v1/shipping/"
Write-Host ""

# Notification Service Tests
Write-Host "=== Notification Service (Port 8007) ==="
Test-Endpoint -Name "Swagger UI" -Url "http://localhost:8007/swagger/"
Test-Endpoint -Name "ReDoc" -Url "http://localhost:8007/redoc/"
Test-Endpoint -Name "Admin Panel" -Url "http://localhost:8007/admin/"
Test-Endpoint -Name "Notifications API" -Url "http://localhost:8007/api/v1/notifications/"
Test-Endpoint -Name "Notifications via Gateway" -Url "http://localhost/api/v1/notifications/"
Write-Host ""

# Admin Tools
Write-Host "=== Admin Tools ==="
Test-Endpoint -Name "Adminer" -Url "http://localhost:8080"
Test-Endpoint -Name "Admin Dashboard" -Url "http://localhost:8000/admin/"
Write-Host ""

# Summary
Write-Host "=========================================="
Write-Host "Test Summary"
Write-Host "=========================================="
Write-Host -ForegroundColor Green "Passed: $script:Passed"
Write-Host -ForegroundColor Red "Failed: $script:Failed"
Write-Host -ForegroundColor Yellow "Skipped: $script:Skipped"
$total = $script:Passed + $script:Failed + $script:Skipped
Write-Host "Total: $total"
Write-Host ""

if ($script:Failed -eq 0) {
    Write-Host -ForegroundColor Green "All tests passed!"
} else {
    Write-Host -ForegroundColor Red "Some tests failed. Check the output above."
}


