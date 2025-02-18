from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="MaiSON Chatbot API",
    description="API for the MaiSON real estate chatbot",
    version="0.1.0",
    root_path="/",  # Add this for proper HTTPS handling
    openapi_url="/openapi.json",
    docs_url="/docs"
)

# Configure CORS with secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://thankful-mud-084a12703.4.azurestaticapps.net",  # Production frontend
        "http://localhost:5137",  # Local development frontend
        "http://localhost:3000",  # Common local development port
        "http://127.0.0.1:5137",  # Alternative local development URL
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS", "HEAD"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
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