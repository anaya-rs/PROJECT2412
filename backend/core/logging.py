"""
v 1.1 core logging - application logging configuration
"""

import logging
import sys
from pathlib import Path


def setup_logging():
    """setup application logging"""
    
    # create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # set specific logger levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    logging.info("Logging configured successfully")
