from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="maiSON Chatbot API",
    description="API for the maiSON real estate chatbot",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://maisonfrontenddnsnamelabel.gbamb4drehf6cjdy.northeurope.azurecontainer.io",
        "http://localhost:5137"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],  # Include GET for health checks
    allow_headers=["Content-Type"],
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