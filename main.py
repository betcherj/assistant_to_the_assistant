"""Main application entry point."""
import logging
import uvicorn

from entry_point.api import app
from utils.logging_config import setup_logging

# Set up logging
setup_logging(level=logging.INFO)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

