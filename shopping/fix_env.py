"""
Fix the .env file by adding the SERPAPI_API_KEY
"""
import os
from pathlib import Path


def fix_env():
    """Fix the .env file by adding the SERPAPI_API_KEY"""
    print("Fixing the .env file...")

    # Path to the .env file
    env_path = Path(__file__).parent / ".env"

    # Check if the .env file exists
    if not env_path.exists():
        print(f".env file not found at {env_path}")
        return

    # Read the existing .env file
    with open(env_path, "r") as f:
        env_content = f.read()

    # Check if SERPAPI_API_KEY already exists
    if "SERPAPI_API_KEY=" in env_content:
        print("SERPAPI_API_KEY already exists in the .env file")
        return

    # Add the SERPAPI_API_KEY
    env_content += f"\n# SERPAPI API Key\nSERPAPI_API_KEY=your_serpapi_api_key_here\n"

    # Write the updated .env file
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"Added SERPAPI_API_KEY to {env_path}")
    print("Please replace 'your_serpapi_api_key_here' with your actual SERPAPI API key")


if __name__ == "__main__":
    fix_env()
