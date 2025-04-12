# File: test_api_routes.py
"""
Simple testing script to verify API routes.
"""
import requests
import json
import sys

# Base URL for the API
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

def test_auth_routes():
    """Test authentication routes"""
    print("\n===== Testing Auth Routes =====")
    
    # Test login (will fail with invalid credentials)
    print("\nTesting login (expected to fail with invalid credentials):")
    login_url = f"{BASE_URL}{API_PREFIX}/auth/login"
    login_data = {"username": "testuser", "password": "wrongpassword"}
    try:
        response = requests.post(
            login_url, 
            data={"username": "testuser", "password": "wrongpassword"}
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}...")
    except Exception as e:
        print(f"  Error: {e}")

def test_article_routes():
    """Test article routes"""
    print("\n===== Testing Article Routes =====")
    
    # Test listing articles
    print("\nTesting get articles:")
    articles_url = f"{BASE_URL}{API_PREFIX}/articles/"
    try:
        response = requests.get(articles_url)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test article creation without auth
    print("\nTesting create article without auth (expected to fail):")
    create_url = f"{BASE_URL}{API_PREFIX}/articles/"
    article_data = {
        "title": "Test Article",
        "content": "This is a test article content",
        "summary": "Test summary",
        "categories": ["Test"],
        "tags": ["test"]
    }
    try:
        response = requests.post(
            create_url,
            json=article_data
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:100]}...")
    except Exception as e:
        print(f"  Error: {e}")

def test_page_routes():
    """Test page routes"""
    print("\n===== Testing Page Routes =====")
    
    # Test homepage
    print("\nTesting homepage:")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"  Status: {response.status_code}")
        print(f"  Content type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Response size: {len(response.text)} characters")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test create article page
    print("\nTesting create article page:")
    try:
        response = requests.get(f"{BASE_URL}/create-article")
        print(f"  Status: {response.status_code}")
        print(f"  Content type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Response size: {len(response.text)} characters")
    except Exception as e:
        print(f"  Error: {e}")

def test_all_endpoints():
    """Print all API endpoints for manual testing"""
    print("\n===== API Endpoints for Manual Testing =====")
    
    endpoints = [
        {"method": "POST", "url": f"{BASE_URL}{API_PREFIX}/auth/login", "desc": "Login"},
        {"method": "POST", "url": f"{BASE_URL}{API_PREFIX}/auth/register", "desc": "Register"},
        {"method": "GET", "url": f"{BASE_URL}{API_PREFIX}/auth/me", "desc": "Get current user"},
        
        {"method": "GET", "url": f"{BASE_URL}{API_PREFIX}/articles/", "desc": "List articles"},
        {"method": "POST", "url": f"{BASE_URL}{API_PREFIX}/articles/", "desc": "Create article"},
        {"method": "GET", "url": f"{BASE_URL}{API_PREFIX}/articles/[id]", "desc": "Get article"},
        {"method": "PUT", "url": f"{BASE_URL}{API_PREFIX}/articles/[id]", "desc": "Update article"},
        
        {"method": "GET", "url": f"{BASE_URL}/", "desc": "Homepage"},
        {"method": "GET", "url": f"{BASE_URL}/articles", "desc": "Articles list page"},
        {"method": "GET", "url": f"{BASE_URL}/create-article", "desc": "Create article page"},
        {"method": "GET", "url": f"{BASE_URL}/edit-article/[id]", "desc": "Edit article page"},
    ]
    
    print("\nEndpoints to test:")
    for i, endpoint in enumerate(endpoints, 1):
        print(f"  {i}. {endpoint['method']} {endpoint['url']} - {endpoint['desc']}")

def main():
    print("\n========================================")
    print("Kryptopedia API Routes Testing Script")
    print("========================================")
    
    print("\nThis script will test various API routes to check if they're working correctly.")
    print("Note: Some tests are expected to fail (e.g., auth-required endpoints)")
    
    test_auth_routes()
    test_article_routes()
    test_page_routes()
    test_all_endpoints()
    
    print("\n========================================")
    print("Testing complete!")
    print("========================================")

if __name__ == "__main__":
    main()
