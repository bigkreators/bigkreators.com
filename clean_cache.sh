# Remove any __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove any .pyc files
find . -name "*.pyc" -delete
