#!/usr/bin/env python3
"""
Test runner script for the ML Worker service.

This script runs all worker tests.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all worker tests."""
    print("🤖 Running ML Worker Tests")
    print("=" * 50)
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Install dependencies if needed
    print("📦 Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                  check=False)
    
    # Run tests
    print("\n🔍 Running worker tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_worker",
        "tests/"
    ], capture_output=False)
    
    if result.returncode == 0:
        print("\n✅ All worker tests passed!")
        print("📊 Coverage report generated in htmlcov_worker/index.html")
    else:
        print("\n❌ Some worker tests failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 