"""
Test Runner - Consolidated test execution
"""

import sys
import os
import subprocess
from pathlib import Path


def run_test_suite(test_file, description):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running {description}: {e}")
        return False


def main():
    """Run all test suites"""
    print("🧪 Clean Architecture Test Suite")
    print("Testing all layers: Domain, Services, API, Integration")
    
    test_suites = [
        ("tests/test_domain.py", "Domain Layer Tests"),
        ("tests/test_services.py", "Services Layer Tests"), 
        ("tests/test_api.py", "API Layer Tests"),
        ("tests/test_integration.py", "Integration Tests")
    ]
    
    results = []
    for test_file, description in test_suites:
        success = run_test_suite(test_file, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("💥 Some test suites failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
