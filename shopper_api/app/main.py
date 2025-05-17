from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from .routers import research, orders, promotions, support

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ShopperAI API",
    description="API for ShopperAI - a smart shopping assistant",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(research.router)
app.include_router(orders.router)
app.include_router(promotions.router)
app.include_router(support.router)


@app.get("/")
async def root():
    """
    Root endpoint providing API information
    """
    return {
        "message": "Welcome to ShopperAI API",
        "version": "1.0.0",
        "endpoints": {
            "research": "/research",
            "orders": "/orders",
            "promotions": "/promotions",
            "support": "/support"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={"message": f"An unexpected error occurred: {str(exc)}"},
    )


def start():
    """
    Start the FastAPI server using uvicorn
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )


if __name__ == "__main__":
    start() 