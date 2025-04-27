"""
Setup environment variables for ShopperAI
"""
import os
import sys
from pathlib import Path


def setup_env():
    """Set up environment variables for ShopperAI"""
    print("Setting up environment variables for ShopperAI...")

    # Get the OpenAI API key from the user
    openai_api_key = input("Enter your OpenAI API key: ")

    # Get the SERPAPI API key from the user
    serpapi_api_key = input("Enter your SERPAPI API key: ")

    # Create .env file
    env_path = Path(__file__).parent / ".env"

    with open(env_path, "w") as f:
        f.write(f"# OpenAI API Key\n")
        f.write(f"OPENAI_API_KEY={openai_api_key}\n")
        f.write(f"\n")
        f.write(f"# SERPAPI API Key\n")
        f.write(f"SERPAPI_API_KEY={serpapi_api_key}\n")
        f.write(f"\n")
        f.write(f"# Other environment variables\n")
        f.write(f"# Add any other environment variables your application needs here\n")

    print(f"Created .env file at {env_path}")
    print("Environment variables set up successfully!")


if __name__ == "__main__":
    setup_env()
