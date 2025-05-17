#!/bin/bash

# This script starts the ShopperAI API

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating a template .env file..."
    echo "# ShopperAI API Environment Variables" > .env
    echo "OPENAI_API_KEY=your_openai_api_key" >> .env
    echo "SERPAPI_API_KEY=your_serpapi_api_key" >> .env
    echo "PORT=8000" >> .env
    echo ".env file created. Please edit it with your actual API keys before running the application."
    exit 1
fi

# Install requirements if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the API
echo "Starting ShopperAI API..."
python run.py 