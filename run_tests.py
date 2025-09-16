"""
Test runner for College Recommendation System
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def run_tests():
    """Run all tests"""
    try:
        import pytest
        
        # Run tests
        test_dir = Path(__file__).parent / "tests"
        result = pytest.main([str(test_dir), "-v", "--tb=short"])
        
        if result == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
        return result == 0
        
    except ImportError:
        print("❌ pytest not installed. Install with: pip install pytest")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
