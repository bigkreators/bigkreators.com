#!/usr/bin/env python3
"""
Kryptopedia Diagnostic Script
This script checks the basic configuration of your Kryptopedia installation
and helps troubleshoot common issues.
"""
import os
import sys
import requests
from pathlib import Path
import shutil

def print_header(text):
    print(f"\n{'=' * 50}")
    print(f" {text}")
    print(f"{'=' * 50}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_warning(text):
    print(f"⚠️ {text}")

def print_info(text):
    print(f"ℹ️ {text}")

def check_directory_structure():
    print_header("Checking Directory Structure")
    
    required_dirs = [
        "static",
        "templates",
        "media",
        "models",
        "routes",
        "services",
        "dependencies",
        "utils"
    ]
    
    for directory in required_dirs:
        if os.path.isdir(directory):
            print_success(f"Directory '{directory}' exists")
        else:
            print_error(f"Directory '{directory}' is missing")
            
    # Check for essential files
    essential_files = [
        "main.py",
        "config.py",
        "static/style.css",
        "templates/base.html"
    ]
    
    for file_path in essential_files:
        if os.path.isfile(file_path):
            print_success(f"File '{file_path}' exists")
        else:
            print_error(f"File '{file_path}' is missing")

def check_static_files():
    print_header("Checking Static Files")
    
    css_file = Path("static/style.css")
    if css_file.exists():
        size = css_file.stat().st_size
        print_info(f"style.css size: {size} bytes")
        
        if size < 100:
            print_warning("style.css file seems too small, might be empty or corrupted")
        elif size > 1000:
            print_success("style.css file size looks good")
    else:
        print_error("style.css file is missing")
        
        # Create the static directory if it doesn't exist
        if not os.path.exists('static'):
            os.makedirs('static')
            print_info("Created 'static' directory")
        
        print_info("You need to create a style.css file in the static directory")

def check_templates():
    print_header("Checking Templates")
    
    base_template = Path("templates/base.html")
    if base_template.exists():
        content = base_template.read_text(encoding='utf-8')
        
        # Check for critical elements
        checks = [
            ("<link rel=\"stylesheet\" href=\"/static/style.css\">", "CSS link"),
            ("<header>", "Header tag"),
            ("<div class=\"container\">", "Container div"),
            ("<div class=\"sidebar\">", "Sidebar div"),
            ("<div class=\"main-content\">", "Main content div"),
            ("<footer>", "Footer tag")
        ]
        
        for pattern, name in checks:
            if pattern in content:
                print_success(f"Found {name} in base template")
            else:
                print_error(f"Missing {name} in base template")
    else:
        print_error("base.html template is missing")

def check_server_status():
    print_header("Checking Server Status")
    
    try:
        response = requests.get("http://localhost:8000", timeout=2)
        print_success(f"Server is responding with status code: {response.status_code}")
        
        # Check if response contains HTML
        if 'text/html' in response.headers.get('Content-Type', ''):
            if '<link rel="stylesheet" href="/static/style.css">' in response.text:
                print_success("CSS link found in homepage HTML")
            else:
                print_error("CSS link not found in homepage HTML")
                
            if '<header>' in response.text:
                print_success("Header tag found in homepage HTML")
            else:
                print_error("Header tag not found in homepage HTML")
    except requests.RequestException:
        print_error("Could not connect to server. Make sure it's running.")

def fix_styling():
    print_header("Applying Emergency Style Fix")
    
    # Path to the emergency CSS file
    emergency_css = """/* Kryptopedia Emergency Style Fix */
/* Basic Reset and Fonts */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f9f9f9;
    padding: 0;
    margin: 0;
}

/* Container Layout */
.container {
    display: flex;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    min-height: calc(100vh - 140px);
}

/* Header Styles */
header {
    background-color: #fff;
    border-bottom: 1px solid #e0e0e0;
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.logo-link {
    text-decoration: none;
    color: inherit;
}

.logo {
    font-size: 24px;
    font-weight: bold;
    color: #333;
}

.search-bar {
    display: flex;
    margin: 0 20px;
    flex-grow: 1;
    max-width: 500px;
}

.search-bar input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #ddd;
    border-radius: 4px 0 0 4px;
    font-size: 14px;
}

.search-bar button {
    padding: 8px 15px;
    background-color: #0645ad;
    color: white;
    border: none;
    border-radius: 0 4px 4px 0;
    cursor: pointer;
}

/* Navigation Styles */
nav ul {
    list-style: none;
    display: flex;
    gap: 15px;
}

nav ul li a {
    text-decoration: none;
    color: #444;
    font-weight: 500;
    padding: 5px 10px;
    border-radius: 4px;
}

nav ul li a:hover {
    background-color: #f0f0f0;
}

nav ul li a.active {
    background-color: #0645ad;
    color: white;
}

/* Sidebar Styles */
.sidebar {
    width: 250px;
    padding-right: 20px;
}

.sidebar h3 {
    margin-top: 20px;
    margin-bottom: 10px;
    font-size: 18px;
    color: #333;
}

.sidebar ul {
    list-style: none;
    margin-bottom: 20px;
}

.sidebar ul li {
    margin-bottom: 8px;
}

.sidebar ul li a {
    text-decoration: none;
    color: #0645ad;
}

.sidebar ul li a:hover {
    text-decoration: underline;
}

/* Main Content Styles */
.main-content {
    flex-grow: 1;
    padding: 0 20px;
}

/* Footer Styles */
footer {
    background-color: #f0f0f0;
    padding: 20px;
    text-align: center;
    border-top: 1px solid #e0e0e0;
    margin-top: auto;
}

footer ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 10px;
}

footer ul li a {
    text-decoration: none;
    color: #555;
}

/* Modal Styles */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.6);
}

.modal-content {
    background-color: #fff;
    margin: 10% auto;
    padding: 25px;
    border-radius: 8px;
    max-width: 500px;
    position: relative;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.close {
    position: absolute;
    right: 15px;
    top: 10px;
    font-size: 24px;
    font-weight: bold;
    cursor: pointer;
    color: #666;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 500;
}

.form-group input, 
.form-group select,
.form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

button {
    padding: 8px 16px;
    background-color: #0645ad;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

button:hover {
    background-color: #053a7a;
}

/* Article Styles */
.article-header {
    margin-bottom: 20px;
}

.article-meta {
    color: #666;
    margin: 10px 0;
    font-size: 14px;
}

.article-meta span {
    margin-right: 15px;
}

.article-content {
    margin-bottom: 30px;
    line-height: 1.7;
}

.article-content h1, 
.article-content h2, 
.article-content h3, 
.article-content h4 {
    margin-top: 1.5em;
    margin-bottom: 0.7em;
}

.article-content p {
    margin-bottom: 1em;
}

.article-content ul, 
.article-content ol {
    margin-left: 2em;
    margin-bottom: 1em;
}

.article-categories, 
.article-tags {
    margin: 15px 0;
}

.category-tag, 
.tag {
    display: inline-block;
    padding: 3px 10px;
    background-color: #f0f0f0;
    border-radius: 12px;
    margin-right: 8px;
    margin-bottom: 8px;
    font-size: 13px;
    color: #555;
    text-decoration: none;
}

.category-tag:hover, 
.tag:hover {
    background-color: #e0e0e0;
}

/* Utility Classes */
.hidden {
    display: none !important;
}

.auth-required {
    display: none;
}

/* Responsive Styles */
@media (max-width: 768px) {
    header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .search-bar {
        margin: 15px 0;
        max-width: 100%;
        width: 100%;
    }
    
    nav ul {
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    .container {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
        padding-right: 0;
        margin-bottom: 20px;
    }
    
    .main-content {
        padding: 0;
    }
}

/* Logo link styles */
.logo-link {
    text-decoration: none;
    color: inherit;
    display: inline-block;
}

.logo-link:hover {
    text-decoration: none;
    color: #0645ad;
}
"""
    
    # Ensure static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
        print_info("Created 'static' directory")
    
    # Backup existing CSS if it exists
    css_path = 'static/style.css'
    if os.path.exists(css_path):
        backup_path = 'static/style.css.bak'
        shutil.copy2(css_path, backup_path)
        print_info(f"Backed up existing CSS to {backup_path}")
    
    # Write emergency CSS
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(emergency_css)
    
    print_success(f"Emergency CSS written to {css_path}")
    print_info("Restart your server for changes to take effect")

def check_base_template():
    print_header("Checking Base Template")
    
    base_template_path = 'templates/base.html'
    if not os.path.exists(base_template_path):
        print_error(f"{base_template_path} does not exist!")
        return
    
    with open(base_template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Critical elements to check
    critical_elements = [
        ('<link rel="stylesheet" href="/static/style.css">', 'CSS link'),
        ('<a href="/" class="logo-link">', 'Logo link'),
        ('<span class="logo">Kryptopedia</span>', 'Logo text'),
    ]
    
    for element, name in critical_elements:
        if element not in content:
            print_error(f"Missing {name} in base template")
            if name == 'Logo link' and '<span class="logo">Kryptopedia</span>' in content:
                print_info("Found logo text but it's not wrapped in a link. Template may need updating.")
        else:
            print_success(f"Found {name} in base template")

def main():
    print_header("Kryptopedia Diagnostic Tool")
    
    check_directory_structure()
    check_static_files()
    check_templates()
    check_base_template()
    
    try:
        check_server_status()
    except:
        print_warning("Server status check skipped - server may not be running")
    
    # Ask to apply emergency fix
    print_header("Apply Emergency Fix?")
    print_info("This will overwrite your current style.css file with an emergency version")
    print_info("A backup will be created first")
    
    choice = input("Apply emergency fix? (y/n): ").strip().lower()
    if choice == 'y':
        fix_styling()
        print_header("Next Steps")
        print_info("1. Restart your Kryptopedia server")
        print_info("2. Clear your browser cache or use incognito mode")
        print_info("3. Visit http://localhost:8000 to check if the UI is fixed")
    else:
        print_info("Emergency fix not applied")
    
    print_header("Diagnostic Complete")

if __name__ == "__main__":
    main()
