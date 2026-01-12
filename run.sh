#!/bin/bash
# Convenience script to run the learn_flow Streamlit app
# Usage: ./run.sh

set -e  # Exit on error

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Please copy .env.example to .env and configure your API keys"
    exit 1
fi

# Run the Streamlit app
echo "🚀 Starting learn_flow Streamlit app..."
streamlit run src/ui/app.py
