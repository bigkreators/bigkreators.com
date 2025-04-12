# File: utils/template_filters.py
"""
Template filters for the Kryptopedia application.
"""
from datetime import datetime
from typing import Optional, Any
import re
import html

def strftime_filter(date: Any, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format a datetime object for Jinja2 templates.
    
    Args:
        date: The datetime object, string, or timestamp
        format_str: The strftime format string
        
    Returns:
        str: The formatted date string
    """
    if not date:
        return ""
    
    # Convert string to datetime if needed
    if isinstance(date, str):
        try:
            # Try to parse ISO format date
            from dateutil import parser
            date = parser.parse(date)
        except:
            return date
    
    # Convert timestamp to datetime if needed
    if isinstance(date, (int, float)):
        try:
            date = datetime.fromtimestamp(date)
        except:
            return str(date)
    
    # Format the datetime
    if isinstance(date, datetime):
        return date.strftime(format_str)
    
    # Return as string if all else fails
    return str(date)

def truncate_filter(text: str, length: int = 100, ellipsis: str = '...') -> str:
    """
    Truncate text to a specified length.
    
    Args:
        text: The text to truncate
        length: Maximum length
        ellipsis: String to append to truncated text
        
    Returns:
        str: The truncated text
    """
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    # Truncate to length minus ellipsis length
    truncated = text[:length - len(ellipsis)]
    
    # Find the last space to avoid cutting words
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + ellipsis

def strip_html_filter(text: str) -> str:
    """
    Strip HTML tags from text.
    
    Args:
        text: The HTML text to strip
        
    Returns:
        str: The text with HTML tags removed
    """
    if not text:
        return ""
    
    import re
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Replace multiple whitespace with single space
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    # Trim whitespace
    clean_text = clean_text.strip()
    
    return clean_text

def format_number_filter(number: Any, decimals: int = 0, thousands_sep: str = ',') -> str:
    """
    Format a number with thousands separator and decimal places.
    
    Args:
        number: The number to format
        decimals: Number of decimal places
        thousands_sep: Thousands separator character
        
    Returns:
        str: The formatted number
    """
    if number is None:
        return ""
    
    try:
        number = float(number)
        
        # Format with specified decimal places
        format_str = f"{{:,.{decimals}f}}"
        formatted = format_str.format(number)
        
        # Replace default separator with custom one if needed
        if thousands_sep != ',':
            formatted = formatted.replace(',', thousands_sep)
            
        return formatted
    except (ValueError, TypeError):
        return str(number)

def safe_code_blocks_filter(text: str) -> str:
    """
    Safely escape code blocks in text to prevent rendering issues.
    
    Args:
        text: The text that may contain code blocks
        
    Returns:
        str: Text with safely escaped code blocks
    """
    if not text:
        return ""
    
    # Fix markdown-style code blocks
    pattern = r'```(\w*)\n(.*?)```'
    replacement = r'<pre><code class="language-\1">\2</code></pre>'
    
    # Replace with re.DOTALL to match across multiple lines
    result = re.sub(pattern, replacement, text, flags=re.DOTALL)
    
    return result
