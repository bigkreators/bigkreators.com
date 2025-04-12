# File: template_engine.py
"""
Template engine module for Kryptopedia.
Creates a single shared instance of Jinja2Templates to be used throughout the application.
"""
import os
import logging
from fastapi.templating import Jinja2Templates
import config

# Configure logging
logger = logging.getLogger(__name__)

# Make sure template directory exists
os.makedirs(config.TEMPLATES_DIR, exist_ok=True)

# Create a singleton instance of Jinja2Templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Import utils after templates is defined to avoid circular imports
try:
    from utils.template_filters import (
        strftime_filter, 
        truncate_filter, 
        strip_html_filter, 
        format_number_filter,
        safe_code_blocks_filter
    )

    # Register all template filters
    templates.env.filters["strftime"] = strftime_filter
    templates.env.filters["truncate"] = truncate_filter
    templates.env.filters["strip_html"] = strip_html_filter
    templates.env.filters["format_number"] = format_number_filter
    templates.env.filters["safe_code_blocks"] = safe_code_blocks_filter

    logger.info(f"Template filters registered: {list(templates.env.filters.keys())}")
except Exception as e:
    logger.error(f"Failed to register template filters: {e}")
