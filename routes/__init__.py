# File: routes/__init__.py

try:
    from . import auth
except ImportError as e:
    print(f"Warning: Could not import auth routes: {e}")

try:
    from . import articles
except ImportError as e:
    print(f"Warning: Could not import articles routes: {e}")

try:
    from . import media
except ImportError as e:
    print(f"Warning: Could not import media routes: {e}")

try:
    from . import proposals
except ImportError as e:
    print(f"Warning: Could not import proposals routes: {e}")

try:
    from . import rewards
except ImportError as e:
    print(f"Warning: Could not import rewards routes: {e}")

try:
    from . import special
except ImportError as e:
    print(f"Warning: Could not import special routes: {e}")

try:
    from . import profile
except ImportError as e:
    print(f"Warning: Could not import profile routes: {e}")

try:
    from . import media_additional
except ImportError as e:
    print(f"Warning: Could not import media_additional routes: {e}")

try:
    from . import preview
except ImportError as e:
    print(f"Warning: Could not import preview routes: {e}")

try:
    from . import votes
except ImportError as e:
    print(f"Warning: Could not import votes routes: {e}")

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
    'profile',
    'media_additional',
    'preview',
    'votes',
    'page_routes'
]
