# File: /mnt/user-data/outputs/search_json_files_only.py

#!/usr/bin/env python3
"""
JSON Files HTML Comment Scanner

This script searches ONLY .json files for HTML comment syntax (<!-- and -->)
to find the exact JSON file causing your "Unexpected token '<'" error.

Version: 1.0
Author: Claude Assistant
Date: September 26, 2025
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

class JSONCommentScanner:
    def __init__(self, root_directory: str = "."):
        self.root_directory = Path(root_directory)
        self.contaminated_json_files = []
        self.total_json_files = 0
        
        # Directories to skip
        self.skip_directories = {
            '.git', '.svn', 'node_modules', '__pycache__',
            'venv', 'env', 'build', 'dist',
            'usr', 'etc', 'var', 'tmp',
            '.npm', '.npm-global', '.cache', '.local'
        }
    
    def should_skip_directory(self, directory: Path) -> bool:
        """Check if directory should be skipped"""
        return any(skip_dir in directory.parts for skip_dir in self.skip_directories)
    
    def scan_json_file(self, json_file: Path) -> Dict[str, Any]:
        """Scan a single JSON file for HTML comments"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for HTML comment patterns
            html_comment_patterns = [
                r'<!--.*?-->',           # Complete HTML comments
                r'<!--[^>]*$',           # Unclosed HTML comments at end
                r'^[^<]*-->',            # Closing comment at start
                r'<!--\s*File:',         # Specific file header pattern
            ]
            
            found_comments = []
            
            for pattern in html_comment_patterns:
                matches = list(re.finditer(pattern, content, re.DOTALL | re.IGNORECASE | re.MULTILINE))
                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get context around the match
                    start_context = max(0, match.start() - 100)
                    end_context = min(len(content), match.end() + 100)
                    context = content[start_context:end_context]
                    
                    found_comments.append({
                        'pattern': pattern,
                        'match': match.group(),
                        'line': line_num,
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'context': context
                    })
            
            if found_comments:
                # Try to parse as JSON to see the exact error
                parse_error = None
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    parse_error = str(e)
                
                return {
                    'file': str(json_file),
                    'file_size': json_file.stat().st_size,
                    'comments_found': len(found_comments),
                    'comments': found_comments,
                    'parse_error': parse_error,
                    'content_preview': content[:300] + "..." if len(content) > 300 else content,
                    'first_200_chars': content[:200],
                    'last_200_chars': content[-200:] if len(content) > 200 else content
                }
            
        except Exception as e:
            return {
                'file': str(json_file),
                'error': f"Failed to read file: {e}",
                'file_exists': json_file.exists(),
                'file_size': json_file.stat().st_size if json_file.exists() else 0
            }
        
        return None
    
    def find_all_json_files(self) -> List[Path]:
        """Find all JSON files in the directory tree"""
        json_files = []
        
        print(f"🔍 Searching for .json files in {self.root_directory}")
        
        for file_path in self.root_directory.rglob('*.json'):
            # Skip directories and non-files
            if not file_path.is_file():
                continue
            
            # Skip system/dependency directories
            if self.should_skip_directory(file_path):
                print(f"⏭️ Skipping: {file_path} (in excluded directory)")
                continue
            
            json_files.append(file_path)
            print(f"📄 Found JSON file: {file_path}")
        
        return json_files
    
    def scan_all_json_files(self):
        """Scan all JSON files for HTML comments"""
        print("🔍 JSON Files HTML Comment Scanner")
        print("=" * 50)
        
        # Find all JSON files
        json_files = self.find_all_json_files()
        self.total_json_files = len(json_files)
        
        print(f"\n📊 Found {self.total_json_files} JSON files to scan")
        print("-" * 50)
        
        if self.total_json_files == 0:
            print("❌ No JSON files found in project directory")
            return
        
        # Scan each JSON file
        for i, json_file in enumerate(json_files, 1):
            print(f"\n🔍 Scanning {i}/{self.total_json_files}: {json_file}")
            
            result = self.scan_json_file(json_file)
            
            if result and 'comments_found' in result:
                self.contaminated_json_files.append(result)
                print(f"🚨 CONTAMINATION FOUND!")
                print(f"   📁 File: {result['file']}")
                print(f"   💾 Size: {result['file_size']:,} bytes")
                print(f"   🏷️ HTML Comments: {result['comments_found']}")
                
                if result['parse_error']:
                    print(f"   ❌ JSON Parse Error: {result['parse_error']}")
                
                # Show first few comments
                for j, comment in enumerate(result['comments'][:3]):
                    print(f"   📝 Comment {j+1} (Line {comment['line']}): {comment['match'][:80]}...")
                
                print(f"   👀 File starts with: {result['first_200_chars'][:100]}...")
                
            elif result and 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Clean JSON file (no HTML comments)")
    
    def generate_report(self) -> str:
        """Generate a detailed report"""
        report = f"""# JSON Files HTML Comment Report

## Summary
- **Total JSON files found**: {self.total_json_files}
- **Contaminated JSON files**: {len(self.contaminated_json_files)}
- **Clean JSON files**: {self.total_json_files - len(self.contaminated_json_files)}

"""
        
        if self.contaminated_json_files:
            report += f"## 🚨 CONTAMINATED JSON FILES ({len(self.contaminated_json_files)} found)\n\n"
            report += "**These files contain HTML comment syntax and will cause JSON parsing errors!**\n\n"
            
            for i, file_result in enumerate(self.contaminated_json_files, 1):
                report += f"### {i}. {file_result['file']}\n\n"
                report += f"- **File size**: {file_result['file_size']:,} bytes\n"
                report += f"- **HTML comments found**: {file_result['comments_found']}\n"
                
                if file_result.get('parse_error'):
                    report += f"- **JSON Parse Error**: `{file_result['parse_error']}`\n"
                
                report += f"\n**HTML Comments Found:**\n"
                for j, comment in enumerate(file_result['comments']):
                    report += f"{j+1}. Line {comment['line']}: `{comment['match']}`\n"
                
                report += f"\n**File Preview (first 200 characters):**\n```\n{file_result['first_200_chars']}\n```\n"
                
                if len(file_result.get('last_200_chars', '')) > 0:
                    report += f"\n**File End (last 200 characters):**\n```\n{file_result['last_200_chars']}\n```\n"
                
                report += "\n---\n\n"
            
            report += """## 🔧 How to Fix These Files

For each contaminated JSON file above:

1. **Remove HTML comments**: Delete all `<!-- -->` content
2. **Validate JSON syntax**: Ensure proper JSON format
3. **Test parsing**: Use `python -m json.tool filename.json` to validate
4. **Backup first**: Always backup before modifying

## Example Fix:
```bash
# Before (BROKEN):
<!-- File: config.json -->
{"title": "My Article", "slug": "my-article"}

# After (FIXED):
{"title": "My Article", "slug": "my-article"}
```
"""
        else:
            report += """## ✅ NO CONTAMINATED JSON FILES FOUND

All JSON files in your project are clean and don't contain HTML comment syntax.

This means your "Unexpected token '<'" error is likely caused by:

1. **Runtime contamination**: HTML comments added during API response generation
2. **Template mixing**: Template content accidentally included in JSON responses  
3. **Cached responses**: Contaminated data in cache or temporary storage
4. **External data**: JSON data coming from external sources with HTML content

## Next Steps:
1. Use the JavaScript debug code to capture the exact server response
2. Check your API routes for template contamination
3. Look for any template rendering in JSON API endpoints
4. Clear any caches that might contain contaminated data
"""
        
        report += f"""
---
*Report generated by JSON Files HTML Comment Scanner v1.0*  
*Scan completed for: {self.root_directory.absolute()}*
"""
        
        return report
    
    def save_report(self, filename: str = "json_contamination_report.md"):
        """Save the report to a file"""
        report = self.generate_report()
        report_path = Path(filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📊 Detailed report saved to: {report_path.absolute()}")
        return report_path

def main():
    print("🎯 JSON Files ONLY - HTML Comment Scanner")
    print("Searching exclusively for .json files with HTML comment syntax")
    print("=" * 60)
    
    # Initialize and run the scanner
    scanner = JSONCommentScanner()
    scanner.scan_all_json_files()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 SCAN RESULTS:")
    print(f"   📄 Total JSON files: {scanner.total_json_files}")
    print(f"   🚨 Contaminated files: {len(scanner.contaminated_json_files)}")
    print(f"   ✅ Clean files: {scanner.total_json_files - len(scanner.contaminated_json_files)}")
    
    # Save detailed report
    report_path = scanner.save_report()
    
    # Final recommendations
    if scanner.contaminated_json_files:
        print(f"\n🎯 ACTION REQUIRED:")
        print(f"   Remove HTML comments from {len(scanner.contaminated_json_files)} JSON files")
        print(f"   This will fix your 'Unexpected token' JSON parsing error")
    else:
        print(f"\n✅ ALL JSON FILES ARE CLEAN!")
        print(f"   Your error is caused by runtime contamination, not stored files")
    
    print(f"\n📄 Full details in: {report_path.name}")

if __name__ == "__main__":
    main()
