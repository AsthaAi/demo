"""
Directory Initialization Script
Ensures all required directories exist for the shopping system
"""
import os


def init_directories():
    """Initialize all required directories"""
    required_dirs = [
        'shopping/logs',
        'shopping/data',
        'shopping/utils',
        'shopping/agents',
        'shopping/tests',
        'shopping/docs'
    ]

    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")


if __name__ == "__main__":
    init_directories()
