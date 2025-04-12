# File: test_article_edit.py
"""
Script to test the article editing functionality of the Kryptopedia application.
"""
import requests
import json
import sys
import logging
from typing import Dict, Any, Optional
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

def login(username: str, password: str) -> Optional[str]:
    """
    Log in to the application and return an access token.
    
    Args:
        username: Username or email
        password: Password
        
    Returns:
        str: Access token if successful, None otherwise
    """
    try:
        login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
        response = requests.post(
            login_url,
            data={
                "username": username,
                "password": password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Login successful for user: {username}")
            return data.get("access_token")
        else:
            logger.error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return None

def get_user_info(token: str) -> Dict[str, Any]:
    """
    Get information about the current user.
    
    Args:
        token: Access token
        
    Returns:
        Dict: User information
    """
    try:
        me_url = f"{BASE_URL}{API_PREFIX}/auth/me"
        response = requests.get(
            me_url,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Got user info: {data.get('username')}")
            return data
        else:
            logger.error(f"Failed to get user info: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return {}

def get_article(article_id: str) -> Dict[str, Any]:
    """
    Get an article by ID.
    
    Args:
        article_id: Article ID
        
    Returns:
        Dict: Article data
    """
    try:
        article_url = f"{BASE_URL}{API_PREFIX}/articles/{article_id}"
        response = requests.get(article_url)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Got article: {data.get('title')}")
            return data
        else:
            logger.error(f"Failed to get article: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        return {}

def update_article(article_id: str, update_data: Dict[str, Any], token: str) -> bool:
    """
    Update an article.
    
    Args:
        article_id: Article ID
        update_data: Data to update
        token: Access token
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    try:
        update_url = f"{BASE_URL}{API_PREFIX}/articles/{article_id}"
        response = requests.put(
            update_url,
            json=update_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Updated article: {data.get('title')}")
            return True
        else:
            logger.error(f"Failed to update article: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        traceback.print_exc()
        return False

def create_test_article(token: str) -> Optional[str]:
    """
    Create a test article.
    
    Args:
        token: Access token
        
    Returns:
        str: Article ID if successful, None otherwise
    """
    try:
        create_url = f"{BASE_URL}{API_PREFIX}/articles/"
        article_data = {
            "title": "Test Article for Editing",
            "content": "<h1>Test Article</h1><p>This is a test article for editing.</p>",
            "summary": "A test article for testing the editing functionality",
            "categories": ["Test"],
            "tags": ["test", "editing"]
        }
        
        response = requests.post(
            create_url,
            json=article_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            logger.info(f"Created test article: {data.get('title')} (ID: {data.get('_id')})")
            return data.get("_id")
        else:
            logger.error(f"Failed to create test article: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating test article: {e}")
        return None

def test_article_editing():
    """
    Test the article editing functionality.
    """
    logger.info("Starting article editing test")
    
    # Step 1: Login as admin
    token = login("admin", "admin123")
    if not token:
        logger.error("Failed to login as admin. Test aborted.")
        return False
    
    # Step 2: Create a test article
    article_id = create_test_article(token)
    if not article_id:
        logger.error("Failed to create test article. Test aborted.")
        return False
    
    # Step 3: Get the article to verify it exists
    article = get_article(article_id)
    if not article:
        logger.error("Failed to get the created article. Test aborted.")
        return False
    
    original_title = article.get("title")
    logger.info(f"Original article title: {original_title}")
    
    # Step 4: Update the article
    update_data = {
        "title": f"{original_title} - Updated",
        "content": "<h1>Updated Test Article</h1><p>This article has been updated.</p>",
        "summary": "An updated test article",
        "editComment": "Updated for testing"
    }
    
    update_success = update_article(article_id, update_data, token)
    if not update_success:
        logger.error("Failed to update article. Test failed.")
        return False
    
    # Step 5: Verify the update
    updated_article = get_article(article_id)
    if not updated_article:
        logger.error("Failed to get the updated article. Test aborted.")
        return False
    
    updated_title = updated_article.get("title")
    logger.info(f"Updated article title: {updated_title}")
    
    if updated_title == update_data["title"]:
        logger.info("Article was successfully updated! Test passed.")
        return True
    else:
        logger.error(f"Article update verification failed. Expected title: {update_data['title']}, got: {updated_title}")
        return False

def main():
    """
    Main function.
    """
    print("=== Kryptopedia Article Editing Test ===")
    print("This script will test the article editing functionality.")
    print("Make sure the application is running at http://localhost:8000")
    
    try:
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/")
            print(f"Server is running: {response.status_code}")
        except requests.ConnectionError:
            print("Error: Cannot connect to server. Make sure it's running at http://localhost:8000")
            return 1
        
        # Run the test
        success = test_article_editing()
        
        if success:
            print("\n✅ Article editing test passed!")
            return 0
        else:
            print("\n❌ Article editing test failed. See logs for details.")
            return 1
    except Exception as e:
        print(f"\n❌ An error occurred during testing: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
