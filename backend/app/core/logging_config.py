"""Centralized Logging Configuration for BuildIQ Pile Takeoff Engine.

Provides unified, formatted loggers with timestamp, log level, module name,
and structured step markers for engineering calculations, LLM inputs/outputs,
CAD vector processing, and pipeline orchestration.
"""

import sys
import logging
from typing import Optional


def setup_logger(name: str = "buildiq", level: Optional[int] = None) -> logging.Logger:
    """Create or retrieve a configured logger instance with standard formatting."""
    logger = logging.getLogger(name)
    
    if level is None:
        level = logging.INFO
        
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger is already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Standardized formatter with timestamp, level, name, and message
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger


# Specialized component loggers
app_logger = setup_logger("buildiq.app")
calc_logger = setup_logger("buildiq.calculator")
nim_logger = setup_logger("buildiq.nim_vision")
dxf_logger = setup_logger("buildiq.dxf_parser")
pdf_logger = setup_logger("buildiq.pdf_parser")
pipeline_logger = setup_logger("buildiq.pipeline")
exporter_logger = setup_logger("buildiq.exporter")
api_logger = setup_logger("buildiq.api")
