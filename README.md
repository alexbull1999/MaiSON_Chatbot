# maiSON Chatbot Microservice

This is a microservice for a chatbot application built with FastAPI.

## Getting Started

1. Install dependencies: pip install -r requirements.txt
2. Create a .env file based on .env.example
3. Run the server: uvicorn app.main:app --reload

## Docker

Build the Docker image:

    docker build -t maison_chatbot .

## Testing

Run tests with:

    pytest

## Documentation

See the docs/ folder for more details. 