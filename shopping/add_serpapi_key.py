"""
Add SERPAPI API key to the .env file
"""
import os
from pathlib import Path


def add_serpapi_key():
    """Add SERPAPI API key to the .env file"""
    print("Adding SERPAPI API key to the .env file...")

    # Get the SERPAPI API key from the user
    serpapi_api_key = input("Enter your SERPAPI API key: ")

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
        # Replace the existing SERPAPI_API_KEY
        lines = env_content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("SERPAPI_API_KEY="):
                lines[i] = f"SERPAPI_API_KEY={serpapi_api_key}"
                break
        env_content = "\n".join(lines)
    else:
        # Add the SERPAPI_API_KEY
        env_content += f"\n# SERPAPI API Key\nSERPAPI_API_KEY={serpapi_api_key}\n"

    # Write the updated .env file
    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"Added SERPAPI API key to {env_path}")
    print("SERPAPI API key added successfully!")


if __name__ == "__main__":
    add_serpapi_key()
