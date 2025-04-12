try:
    from . import special
except ImportError as e:
    print(f"Warning: Could not import special routes: {e}")

try:
    from . import page_routes
except ImportError as e:
    print(f"Warning: Could not import page routes: {e}")

# Export modules
__all__ = [
    'auth',
    'articles',
    'media',
    'proposals',
    'rewards',
    'special',
    'page_routes'
]
