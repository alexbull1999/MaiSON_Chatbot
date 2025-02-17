from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="MaiSON Chatbot API",
    description="API for the MaiSON real estate chatbot",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://maisonfrontenddnsnamelabel.gbamb4drehf6cjdy.northeurope.azurecontainer.io",
        "http://localhost:5137"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],  # Added OPTIONS for preflight requests
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to maiSON Chatbot API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    } 