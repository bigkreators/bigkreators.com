# File: main.py (excerpt)
"""
Main entry point for the Kryptopedia application.
This is just the relevant section for initializing search at startup.
"""
import logging
from fastapi import FastAPI

# ... other imports ...
import config
from services.database import Database

# Configure logging
logger = logging.getLogger("kryptopedia")

# Initialize FastAPI app
app = FastAPI(
    title="Kryptopedia API",
    description="API for Kryptopedia Wiki",
    version="0.1.0",
    debug=config.API_DEBUG
)

# ... other app configuration ...

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.
    """
    try:
        # Connect to database
        await db_service.connect()
        logger.info(f"Connected to database: {config.DB_NAME}")
        
        # Create required directories
        # ... other initialization code ...
        
        # Initialize search index if needed - FIXED VERSION
        if config.USE_ELASTICSEARCH:
            try:
                from services.search.elasticsearch import ElasticsearchSearch
                
                # Create and initialize the search service directly
                search_service = ElasticsearchSearch(es_host=config.ES_HOST)
                
                # Create necessary indices
                await search_service.create_index("articles", {
                    "properties": {
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "summary": {"type": "text"},
                        "categories": {"type": "keyword"},
                        "tags": {"type": "keyword"}
                    }
                })
                logger.info("Elasticsearch indices initialized")
                
                # Close the connection
                await search_service.close()
            except Exception as e:
                logger.warning(f"Search service initialization error: {e}")
                
        logger.info(f"Kryptopedia is running in {'production' if not config.API_DEBUG else 'development'} mode")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
