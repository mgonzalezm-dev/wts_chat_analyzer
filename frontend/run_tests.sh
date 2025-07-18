#!/bin/bash

# Frontend Test Runner Script

echo "🧪 Running Frontend Tests..."
echo "=========================="

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run tests based on argument
case "$1" in
    "unit")
        echo "Running unit tests..."
        npm run test -- --run
        ;;
    "watch")
        echo "Running tests in watch mode..."
        npm run test
        ;;
    "coverage")
        echo "Running tests with coverage..."
        npm run test:coverage
        ;;
    "ui")
        echo "Opening test UI..."
        npm run test:ui
        ;;
    *)
        echo "Running all tests..."
        npm run test -- --run
        ;;
esac

echo "✅ Test run complete!"