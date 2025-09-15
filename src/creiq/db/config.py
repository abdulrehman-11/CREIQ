"""
Database configuration for the CREIQ application.

This module handles database connection configuration through environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default to SQLite
DEFAULT_DATABASE_URL = "sqlite:///creiq.db"

# Get database connection string from environment variable or use default
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Get database logging level from environment variable or use default
DATABASE_LOG_LEVEL = os.getenv("DATABASE_LOG_LEVEL", "WARNING")