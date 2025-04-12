#!/usr/bin/env python3
"""
Script to replace "Cryptopedia" with "Kryptopedia" in all template files
and update the logo to be a clickable link to the home page.
"""
import os
import re

# Directory containing the templates
TEMPLATES_DIR = "templates"

# List of file extensions to process
EXTENSIONS = [".html"]

# Counters for statistics
files_processed = 0
files_modified = 0
replacements_made = 0

# Function to update the header
def update_header(content):
    """Replace the header with a new one that has a clickable logo."""
    header_pattern = re.compile(r'<header>.*?<span class="logo">Cryptopedia</span>.*?</header>', re.DOTALL)
    new_header = """<header>
    <a href="/" class="logo-link">
        <span class="logo">Kryptopedia</span>
    </a>
    
    <div class="search-bar">
        <input type="text" id="search-input" placeholder="Search the wiki...">
        <button id="search-button">Search</button>
    </div>
    
    <nav>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/articles">Articles</a></li>
            <li><a href="/api/articles/random" id="random-article">Random</a></li>
            <li><a href="/contribute" id="contribute-link">Contribute</a></li>
            <li><a href="#" id="login-link">Login</a></li>
        </ul>
    </nav>
</header>"""
    
    # Check if we have a match
    if header_pattern.search(content):
        content = header_pattern.sub(new_header, content)
        return content, True
    return content, False

# Function to update the footer
def update_footer(content):
    """Replace the footer with "Kryptopedia" instead of "Cryptopedia"."""
    footer_pattern = re.compile(r'<footer>.*?Cryptopedia.*?</footer>', re.DOTALL)
    new_footer = """<footer>
    <p>Kryptopedia - A collaborative knowledge base</p>
    <ul>
        <li><a href="/about">About</a></li>
        <li><a href="/privacy">Privacy Policy</a></li>
        <li><a href="/terms">Terms of Use</a></li>
        <li><a href="/contact">Contact</a></li>
    </ul>
</footer>"""
    
    # Check if we have a match
    if footer_pattern.search(content):
        content = footer_pattern.sub(new_footer, content)
        return content, True
    return content, False

# Function to update page titles
def update_titles(content):
    """Replace "Cryptopedia" with "Kryptopedia" in page titles."""
    title_pattern = re.compile(r'<title>(.*?)Cryptopedia(.*?)</title>')
    
    # Function to replace the title while preserving the rest
    def replace_title(match):
        return f'<title>{match.group(1)}Kryptopedia{match.group(2)}</title>'
    
    # Count how many replacements we make
    new_content, count = re.subn(title_pattern, replace_title, content)
    return new_content, count > 0

# Function to update any remaining instances
def update_remaining(content):
    """Replace any remaining instances of "Cryptopedia" with "Kryptopedia"."""
    # Avoid replacing content that's already been handled by more specific functions
    pattern = re.compile(r'Cryptopedia')
    
    # Count how many replacements we make
    new_content, count = re.subn(pattern, 'Kryptopedia', content)
    return new_content, count

def process_file(file_path):
    """Process a single file to update branding."""
    global files_processed, files_modified, replacements_made
    
    files_processed += 1
    modified = False
    replacements = 0
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update header
    content, header_updated = update_header(content)
    if header_updated:
        modified = True
        replacements += 1
    
    # Update footer
    content, footer_updated = update_footer(content)
    if footer_updated:
        modified = True
        replacements += 1
    
    # Update page titles
    content, titles_updated = update_titles(content)
    if titles_updated:
        modified = True
        replacements += 1
    
    # Update any remaining instances
    content, count = update_remaining(content)
    if count > 0:
        modified = True
        replacements += count
    
    # Write the updated content back to the file if it was modified
    if modified:
        files_modified += 1
        replacements_made += replacements
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path} ({replacements} replacements)")

def process_directory(directory):
    """Process all files in the directory that match our criteria."""
    for root, _, files in os.walk(directory):
        for file in files:
            # Check if the file has an extension we're interested in
            if any(file.endswith(ext) for ext in EXTENSIONS):
                file_path = os.path.join(root, file)
                process_file(file_path)

def update_css():
    """Add the logo link CSS to style.css."""
    css_path = "static/style.css"
    
    # Check if the file exists
    if not os.path.exists(css_path):
        print(f"Warning: {css_path} not found. CSS for logo link not added.")
        return
    
    # Read the current CSS content
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check if the logo-link class already exists
    if ".logo-link" in css_content:
        print("Logo link CSS already exists in style.css")
        return
    
    # Add the new CSS
    logo_css = """
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

.logo {
    font-size: 24px;
    font-weight: bold;
    color: #333;
}
"""
    
    # Append the CSS to the file
    with open(css_path, 'a', encoding='utf-8') as f:
        f.write(logo_css)
    
    print(f"Added logo link CSS to {css_path}")

def main():
    """Main function to run the script."""
    print(f"Starting to process template files in {TEMPLATES_DIR}...")
    
    # Process all files in the templates directory
    if os.path.exists(TEMPLATES_DIR):
        process_directory(TEMPLATES_DIR)
    else:
        print(f"Error: {TEMPLATES_DIR} directory not found.")
        return
    
    # Update the CSS file
    update_css()
    
    # Print summary
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")
    print(f"Total replacements made: {replacements_made}")
    print(f"Logo link CSS added to style.css")
    print("\nBranding update complete!")

if __name__ == "__main__":
    main()
