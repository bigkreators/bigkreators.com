# File: debug_dependencies.py
"""
Diagnostic tool for troubleshooting FastAPI dependency issues in Kryptopedia.
This script checks dependencies for common issues and provides guidance on fixing them.
"""
import inspect
import importlib
import sys
import os
from typing import Dict, List, Any, Optional, Set, Tuple

# ANSI color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_color(text: str, color: str) -> None:
    """Print text with specified color."""
    print(f"{color}{text}{ENDC}")

def scan_directory(directory: str) -> List[str]:
    """Scan directory for Python files."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def is_dependency_function(func) -> bool:
    """Check if a function is a FastAPI dependency function."""
    if not inspect.isfunction(func):
        return False
    
    # Check for common patterns in FastAPI dependencies
    sig = inspect.signature(func)
    # Check if function has 'Depends' in its parameters
    has_depends = any('Depends' in str(param.annotation) for param in sig.parameters.values())
    # Check if function yield or return value
    is_gen = inspect.isgeneratorfunction(func) or inspect.isasyncgenfunction(func)
    # Check if name suggests it's a dependency
    name_suggests = func.__name__.startswith('get_') or 'dependency' in func.__name__.lower()
    
    return has_depends or is_gen or name_suggests

def analyze_dependency(func) -> Dict[str, Any]:
    """Analyze a potential dependency function for issues."""
    result = {
        "name": func.__name__,
        "is_async": inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func),
        "is_generator": inspect.isgeneratorfunction(func) or inspect.isasyncgenfunction(func),
        "uses_yield": False,
        "issues": [],
        "warnings": [],
        "source_code": inspect.getsource(func),
        "file": inspect.getfile(func),
        "depends_on": []
    }
    
    # Check if function contains yield statement
    source = inspect.getsource(func)
    if "yield" in source:
        result["uses_yield"] = True
    
    # Check for common issues
    if result["is_generator"] and not result["uses_yield"]:
        result["issues"].append("Function is a generator but doesn't use 'yield'")
    
    if result["uses_yield"] and not result["is_generator"]:
        result["issues"].append("Function uses 'yield' but isn't declared as a generator")
    
    if result["is_async"] and not result["is_generator"] and "await" not in source:
        result["issues"].append("Async function doesn't use 'await'")
    
    # Look for potential boolean evaluations of database objects
    if "db" in source and ("if db:" in source or "if not db:" in source):
        result["issues"].append("Potential boolean evaluation of database object (use 'is None' instead)")
    
    # Check for dependencies this function depends on
    sig = inspect.signature(func)
    for param_name, param in sig.parameters.items():
        if 'Depends' in str(param.annotation):
            # Extract the dependency function name
            annotation_str = str(param.annotation)
            dependency_name = annotation_str.split('Depends(')[1].split(')')[0].strip()
            if dependency_name:
                result["depends_on"].append(dependency_name)
    
    # Check for proper resource cleanup in generator dependencies
    if result["is_generator"]:
        if "try:" not in source or "finally:" not in source:
            result["warnings"].append("Generator dependency should use try/finally for cleanup")
        
        if result["is_async"] and "await" not in source.split("finally:")[1]:
            result["warnings"].append("Async generator should await cleanup in finally block")
    
    return result

def check_module_dependencies(module_name: str) -> List[Dict[str, Any]]:
    """Check all dependencies in a module."""
    results = []
    
    try:
        module = importlib.import_module(module_name)
        
        # Find all functions in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and is_dependency_function(obj):
                results.append(analyze_dependency(obj))
                
    except ImportError as e:
        print_color(f"Error importing module {module_name}: {e}", RED)
        
    return results

def check_file_dependencies(file_path: str) -> List[Dict[str, Any]]:
    """Check all dependencies in a Python file."""
    results = []
    
    # Get the module name from the file path
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Add the directory to sys.path temporarily
    dir_path = os.path.dirname(os.path.abspath(file_path))
    if dir_path not in sys.path:
        sys.path.insert(0, dir_path)
    
    try:
        # Try to import the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            print_color(f"Could not import {file_path}", RED)
            return results
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find all functions in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and is_dependency_function(obj):
                results.append(analyze_dependency(obj))
                
    except Exception as e:
        print_color(f"Error analyzing {file_path}: {e}", RED)
        
    return results

def print_analysis_results(results: List[Dict[str, Any]]) -> None:
    """Print the analysis results in a readable format."""
    issue_count = 0
    warning_count = 0
    
    print_color("\n=== FastAPI Dependency Analysis Results ===\n", BLUE)
    
    for result in results:
        has_issues = len(result["issues"]) > 0
        has_warnings = len(result["warnings"]) > 0
        
        # Only print problematic dependencies
        if not has_issues and not has_warnings:
            continue
        
        issue_count += len(result["issues"])
        warning_count += len(result["warnings"])
        
        header = f"Function: {result['name']} ({os.path.basename(result['file'])})"
        print_color(header, RED if has_issues else YELLOW)
        print("-" * len(header))
        
        print(f"  Async: {result['is_async']}")
        print(f"  Generator: {result['is_generator']}")
        print(f"  Uses yield: {result['uses_yield']}")
        
        if result["depends_on"]:
            print(f"  Depends on: {', '.join(result['depends_on'])}")
        
        if has_issues:
            print_color("  Issues:", RED)
            for issue in result["issues"]:
                print_color(f"    - {issue}", RED)
        
        if has_warnings:
            print_color("  Warnings:", YELLOW)
            for warning in result["warnings"]:
                print_color(f"    - {warning}", YELLOW)
        
        print()  # Add a blank line between results
    
    print_color("=== Summary ===", BLUE)
    print_color(f"Found {issue_count} issues and {warning_count} warnings in {len(results)} dependencies.", 
                RED if issue_count > 0 else GREEN)
    
    if issue_count > 0:
        print_color("\nCommon fixes:", BLUE)
        print("1. For boolean checks on database objects:")
        print("   Instead of: if db:")
        print("   Use: if db is not None:")
        print("\n2. For async generator dependencies:")
        print("   Ensure you have proper resource cleanup:")
        print("   ```python")
        print("   async def get_resource():")
        print("       resource = create_resource()")
        print("       try:")
        print("           yield resource")
        print("       finally:")
        print("           await resource.close()")
        print("   ```")

def main():
    print_color("=== FastAPI Dependency Diagnostic Tool ===", BLUE)
    print("This tool analyzes FastAPI dependencies for common issues.")
    
    # Check specific directories
    target_dirs = ["dependencies", "services"]
    all_results = []
    
    for directory in target_dirs:
        if not os.path.exists(directory):
            print_color(f"Directory '{directory}' not found", YELLOW)
            continue
            
        print_color(f"\nScanning '{directory}' directory for dependencies...", BLUE)
        files = scan_directory(directory)
        
        for file in files:
            file_results = check_file_dependencies(file)
            if file_results:
                all_results.extend(file_results)
    
    print_analysis_results(all_results)

if __name__ == "__main__":
    main()
