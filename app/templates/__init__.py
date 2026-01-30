"""
GETOLS Templates Module
Jinja2 template configuration.
"""

from pathlib import Path
from fastapi.templating import Jinja2Templates

# Get templates directory path (this file is in app/templates/)
TEMPLATES_DIR = Path(__file__).parent

# Create Jinja2 templates instance
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Add custom filters and globals
templates.env.globals["app_name"] = "GETOLS"
templates.env.globals["app_version"] = "1.0.0"


def format_datetime(value, format="%Y-%m-%d %H:%M:%S"):
    """Format datetime for display."""
    if value is None:
        return ""
    return value.strftime(format)


def format_power(value):
    """Format optical power value."""
    if value is None:
        return "N/A"
    return f"{value:.2f} dBm"


# Register filters
templates.env.filters["datetime"] = format_datetime
templates.env.filters["power"] = format_power
