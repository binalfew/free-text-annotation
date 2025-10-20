#!/usr/bin/env python3
"""
Comprehensive Test Runner for NLP Pipeline

This script runs all tests in the project and provides a comprehensive report.

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

import unittest
import sys
import os
import time
from pathlib import Path

def discover_and_run_tests():
    """Discover and run all tests in the project."""
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Test modules to run
    test_modules = [
        'test_components',
        'test_corenlp', 
        'test_extraction',
        'test_batch',
        'test_sentence_splitter',
        'test_syntactic_features',
        'test_preprocessing_integration',
        'test_feature_extraction_integration',
        'test_event_extraction_edge_cases',
        'test_batch_processing_edge_cases',
        'test_configuration_validation'
    ]
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    print("="*70)
    print("NLP PIPELINE COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Running {len(test_modules)} test modules...")
    print()
    
    # Load each test module
    for module_name in test_modules:
        try:
            print(f"Loading {module_name}...")
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            print(f"✓ {module_name} loaded successfully")
        except ImportError as e:
            print(f"✗ Failed to import {module_name}: {e}")
        except Exception as e:
            print(f"✗ Error loading {module_name}: {e}")
    
    print()
    print("="*70)
    print("RUNNING TESTS")
    print("="*70)
    
    # Run tests
    start_time = time.time()
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print()
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0

def run_specific_test_category(category):
    """Run tests for a specific category."""
    
    category_tests = {
        'components': [
            'test_components',
            'test_sentence_splitter',
            'test_syntactic_features'
        ],
        'integration': [
            'test_preprocessing_integration',
            'test_feature_extraction_integration',
            'test_extraction'
        ],
        'edge_cases': [
            'test_event_extraction_edge_cases',
            'test_batch_processing_edge_cases'
        ],
        'performance': [
            'test_performance_benchmarks'
        ],
        'validation': [
            'test_configuration_validation',
            'test_output_formatting'
        ],
        'core': [
            'test_corenlp',
            'test_batch'
        ]
    }
    
    if category not in category_tests:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(category_tests.keys())}")
        return False
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Create test suite for category
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    print(f"Running {category} tests...")
    
    for module_name in category_tests[category]:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
        except Exception as e:
            print(f"Error loading {module_name}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run NLP Pipeline tests')
    parser.add_argument('--category', choices=[
        'components', 'integration', 'edge_cases', 
        'performance', 'validation', 'core', 'all'
    ], default='all', help='Test category to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.category == 'all':
        success = discover_and_run_tests()
    else:
        success = run_specific_test_category(args.category)
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
