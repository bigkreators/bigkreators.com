"""
Template engine module for Kryptopedia.
Creates a single shared instance of Jinja2Templates to be used throughout the application.
"""
from fastapi.templating import Jinja2Templates
from utils.template_filters import strftime_filter, truncate_filter, strip_html_filter, format_number_filter
import config

# Create a singleton instance of Jinja2Templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Register all template filters
templates.env.filters["strftime"] = strftime_filter
templates.env.filters["truncate"] = truncate_filter
templates.env.filters["strip_html"] = strip_html_filter
templates.env.filters["format_number"] = format_number_filter

print(f"Template filters registered: {list(templates.env.filters.keys())}")
