from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="MaiSON Chatbot API",
    description="API for the MaiSON real estate chatbot",
    version="0.1.0",
    root_path="",  # Remove the root_path as it's handled by Azure
    openapi_url="/openapi.json",
    docs_url="/docs"
)

# Configure CORS with secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://thankful-mud-084a12703.4.azurestaticapps.net",  # Production frontend
        "https://4.207.106.67",  # Application Gateway IP
        "https://maisonbot-api.xyz",  # Your custom domain
        "http://localhost:5137",  # Local development frontend
        "http://localhost:3000",  # Common local development port
        "http://127.0.0.1:5137",  # Alternative local development URL
        "http://localhost:8137",  # Additional local development port
        "http://127.0.0.1:8137",  # Additional local development URL
        "https://www.maisonai.co.uk"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],  # Allow all headers for development ease
    expose_headers=[
        "Content-Length",
        "Content-Range",
    ],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to MaiSON Chatbot API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    } 