import uvicorn
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path to enable imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variable or use default 8000
    port = int(os.getenv("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
    
    print(f"Server running at http://localhost:{port}")
    print(f"API documentation available at http://localhost:{port}/docs") 