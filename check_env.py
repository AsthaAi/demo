import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required API keys
required_keys = [
    "SERPAPI_API_KEY",
    "AZTP_API_KEY",
    "OPENAI_API_KEY"
]

print("=== Environment Variables Check ===")
for key in required_keys:
    value = os.getenv(key)
    if value:
        # Mask the key for security
        masked_value = value[:4] + "*" * \
            (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
        print(f"{key}: {masked_value} (Set)")
    else:
        print(f"{key}: Not set")

print("\n=== Additional Information ===")
print(f"Python version: {os.sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Try to import the GoogleSearch class to check if it's available
try:
    from serpapi import GoogleSearch
    print("serpapi package is installed and GoogleSearch class is available")
except ImportError:
    print("serpapi package is not installed or GoogleSearch class is not available")
except Exception as e:
    print(f"Error importing GoogleSearch: {str(e)}")
