#!/usr/bin/env python3
"""
Test runner script for the ML Service API.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting."""
    print("Running ML Service API Tests")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent)
    
    print("Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                  check=False)
    
    print("\nRunning tests with coverage...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=80",
        "tests/"
    ], capture_output=False)
    
    if result.returncode == 0:
        print("\nAll tests passed!")
        print("Coverage report generated in htmlcov/index.html")
    else:
        print("\nSome tests failed!")
        return False
    
    return True

def run_specific_test_file(test_file):
    """Run a specific test file."""
    print(f"Running {test_file}")
    print("=" * 50)
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        f"tests/{test_file}"
    ], capture_output=False)
    
    return result.returncode == 0

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        success = run_specific_test_file(test_file)
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 