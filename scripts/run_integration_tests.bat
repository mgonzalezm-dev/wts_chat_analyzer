@echo off
REM Integration Test Runner for WhatsApp Conversation Analyzer (Windows)
REM This script runs all tests across backend, frontend, and E2E

echo ============================================================
echo WhatsApp Conversation Analyzer - Integration Test Suite
echo ============================================================
echo.

REM Test results
set BACKEND_UNIT_PASSED=false
set BACKEND_INTEGRATION_PASSED=false
set FRONTEND_UNIT_PASSED=false
set E2E_PASSED=false

REM Function to print test section
:print_section
echo.
echo ============================================================
echo %~1
echo ============================================================
echo.
goto :eof

REM Check services
call :print_section "Checking Required Services"

REM Check PostgreSQL (Windows)
pg_isready -h localhost -p 5432 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL is running
) else (
    echo [ERROR] PostgreSQL is not running
    echo Please start PostgreSQL before running tests
    exit /b 1
)

REM Check Redis (Windows)
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Redis is running
) else (
    echo [ERROR] Redis is not running
    echo Please start Redis before running tests
    exit /b 1
)

REM Backend Unit Tests
call :print_section "Running Backend Unit Tests"

cd backend
python run_tests.py --type unit --coverage
if %errorlevel% equ 0 (
    echo [OK] Backend unit tests passed
    set BACKEND_UNIT_PASSED=true
) else (
    echo [ERROR] Backend unit tests failed
)
cd ..

REM Backend Integration Tests
call :print_section "Running Backend Integration Tests"

cd backend
python run_tests.py --type integration
if %errorlevel% equ 0 (
    echo [OK] Backend integration tests passed
    set BACKEND_INTEGRATION_PASSED=true
) else (
    echo [ERROR] Backend integration tests failed
)
cd ..

REM Frontend Unit Tests
call :print_section "Running Frontend Unit Tests"

cd frontend

REM Install dependencies if needed
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

call npm run test -- --run
if %errorlevel% equ 0 (
    echo [OK] Frontend unit tests passed
    set FRONTEND_UNIT_PASSED=true
) else (
    echo [ERROR] Frontend unit tests failed
)
cd ..

REM Start services for E2E tests
call :print_section "Starting Services for E2E Tests"

REM Start backend
cd backend
echo Starting backend server...
start /b python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1
cd ..

REM Start frontend
cd frontend
echo Starting frontend dev server...
start /b npm run dev > ..\frontend.log 2>&1
cd ..

REM Wait for services to start
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is running
) else (
    echo [ERROR] Backend failed to start
    type backend.log
    goto :cleanup
)

curl -f http://localhost:5173 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend is running
) else (
    echo [ERROR] Frontend failed to start
    type frontend.log
    goto :cleanup
)

REM E2E Tests
call :print_section "Running E2E Tests with Cypress"

cd frontend
call npm run e2e
if %errorlevel% equ 0 (
    echo [OK] E2E tests passed
    set E2E_PASSED=true
) else (
    echo [ERROR] E2E tests failed
)
cd ..

REM Performance Tests
call :print_section "Running Performance Tests"

echo Testing API response times...

REM Test login endpoint
for /f "delims=" %%i in ('curl -o nul -s -w "%%{time_total}" -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"username\":\"test@example.com\",\"password\":\"testpassword\"}"') do set LOGIN_TIME=%%i

echo Login endpoint: %LOGIN_TIME%s

REM Generate test report
call :print_section "Test Summary Report"

set TOTAL_PASSED=0
set TOTAL_TESTS=4

echo Test Results:
echo =============

if "%BACKEND_UNIT_PASSED%"=="true" (
    echo [OK] Backend Unit Tests: PASSED
    set /a TOTAL_PASSED+=1
) else (
    echo [ERROR] Backend Unit Tests: FAILED
)

if "%BACKEND_INTEGRATION_PASSED%"=="true" (
    echo [OK] Backend Integration Tests: PASSED
    set /a TOTAL_PASSED+=1
) else (
    echo [ERROR] Backend Integration Tests: FAILED
)

if "%FRONTEND_UNIT_PASSED%"=="true" (
    echo [OK] Frontend Unit Tests: PASSED
    set /a TOTAL_PASSED+=1
) else (
    echo [ERROR] Frontend Unit Tests: FAILED
)

if "%E2E_PASSED%"=="true" (
    echo [OK] E2E Tests: PASSED
    set /a TOTAL_PASSED+=1
) else (
    echo [ERROR] E2E Tests: FAILED
)

echo.
echo Overall: %TOTAL_PASSED%/%TOTAL_TESTS% tests passed

REM Generate detailed report file
set REPORT_FILE=test_report_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set REPORT_FILE=%REPORT_FILE: =0%

(
echo WhatsApp Conversation Analyzer - Test Report
echo Generated: %date% %time%
echo.
echo Test Results Summary:
echo ====================
echo Backend Unit Tests: %BACKEND_UNIT_PASSED%
echo Backend Integration Tests: %BACKEND_INTEGRATION_PASSED%
echo Frontend Unit Tests: %FRONTEND_UNIT_PASSED%
echo E2E Tests: %E2E_PASSED%
echo.
echo Coverage Reports:
echo ================
echo Backend coverage report: backend\htmlcov\index.html
echo Frontend coverage report: frontend\coverage\index.html
echo.
echo Performance Metrics:
echo ===================
echo Login endpoint response time: %LOGIN_TIME%s
) > "%REPORT_FILE%"

echo.
echo Detailed report saved to: %REPORT_FILE%

:cleanup
REM Cleanup services
echo Cleaning up services...

REM Kill backend and frontend processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq uvicorn*" >nul 2>&1
taskkill /f /im node.exe /fi "WINDOWTITLE eq vite*" >nul 2>&1

REM Remove log files
if exist backend.log del backend.log
if exist frontend.log del frontend.log

REM Return appropriate exit code
if %TOTAL_PASSED% equ %TOTAL_TESTS% (
    exit /b 0
) else (
    exit /b 1
)