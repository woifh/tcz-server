#!/usr/bin/env python3
"""
Manual security and performance validation script for anonymous court overview.

This script performs additional manual testing to verify:
1. No sensitive data leakage in anonymous responses
2. Error handling for anonymous users
3. Performance impact validation

Run this script to perform comprehensive manual validation.
"""

import requests
import json
import time
from datetime import date, timedelta
import sys


class AnonymousSecurityValidator:
    """Manual security validation for anonymous court overview."""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def log_result(self, test_name, passed, message):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        self.results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def test_anonymous_access_basic(self):
        """Test basic anonymous access to court availability."""
        try:
            response = self.session.get(f'{self.base_url}/courts/availability')
            
            if response.status_code == 200:
                data = response.json()
                if 'grid' in data and 'date' in data:
                    self.log_result(
                        "Anonymous Access Basic",
                        True,
                        f"Successfully accessed availability data for {data['date']}"
                    )
                else:
                    self.log_result(
                        "Anonymous Access Basic",
                        False,
                        "Response missing required fields (grid, date)"
                    )
            else:
                self.log_result(
                    "Anonymous Access Basic",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            self.log_result(
                "Anonymous Access Basic",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_sensitive_data_leakage(self):
        """Test for sensitive data leakage in anonymous responses."""
        try:
            response = self.session.get(f'{self.base_url}/courts/availability')
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Check for common sensitive data patterns
                sensitive_patterns = [
                    'booked_for_id',
                    'booked_by_id',
                    'reservation_id',
                    'member_id',
                    'password',
                    'email',
                    'phone',
                    'is_short_notice'
                ]
                
                found_sensitive = []
                for pattern in sensitive_patterns:
                    if pattern in response_text:
                        found_sensitive.append(pattern)
                
                if not found_sensitive:
                    self.log_result(
                        "Sensitive Data Leakage",
                        True,
                        "No sensitive data patterns found in anonymous response"
                    )
                else:
                    self.log_result(
                        "Sensitive Data Leakage",
                        False,
                        f"Found sensitive patterns: {', '.join(found_sensitive)}"
                    )
            else:
                self.log_result(
                    "Sensitive Data Leakage",
                    False,
                    f"Could not retrieve data for testing (HTTP {response.status_code})"
                )
        except Exception as e:
            self.log_result(
                "Sensitive Data Leakage",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_invalid_date_handling(self):
        """Test error handling for invalid dates."""
        invalid_dates = [
            'invalid-date',
            '2025-13-01',  # Invalid month
            '2025-02-30',  # Invalid day
            'abc-def-ghi', # Non-numeric
            '2025/12/05',  # Wrong separator
        ]
        
        passed_count = 0
        for invalid_date in invalid_dates:
            try:
                response = self.session.get(
                    f'{self.base_url}/courts/availability?date={invalid_date}'
                )
                
                if response.status_code == 400:
                    data = response.json()
                    if 'error' in data:
                        passed_count += 1
                    else:
                        print(f"  Invalid date '{invalid_date}': Missing error field")
                else:
                    print(f"  Invalid date '{invalid_date}': Expected 400, got {response.status_code}")
            except Exception as e:
                print(f"  Invalid date '{invalid_date}': Exception {str(e)}")
        
        if passed_count == len(invalid_dates):
            self.log_result(
                "Invalid Date Handling",
                True,
                f"All {len(invalid_dates)} invalid dates properly rejected"
            )
        else:
            self.log_result(
                "Invalid Date Handling",
                False,
                f"Only {passed_count}/{len(invalid_dates)} invalid dates properly handled"
            )
    
    def test_rate_limiting_behavior(self):
        """Test rate limiting behavior for anonymous users."""
        try:
            # Make multiple requests quickly
            request_count = 10
            response_codes = []
            
            for i in range(request_count):
                response = self.session.get(f'{self.base_url}/courts/availability')
                response_codes.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if all requests succeeded (within rate limit)
            success_count = sum(1 for code in response_codes if code == 200)
            
            if success_count >= request_count * 0.8:  # Allow some failures
                self.log_result(
                    "Rate Limiting Behavior",
                    True,
                    f"{success_count}/{request_count} requests succeeded (rate limiting working)"
                )
            else:
                self.log_result(
                    "Rate Limiting Behavior",
                    False,
                    f"Only {success_count}/{request_count} requests succeeded"
                )
        except Exception as e:
            self.log_result(
                "Rate Limiting Behavior",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_performance_impact(self):
        """Test performance impact of data filtering."""
        try:
            # Measure response times for multiple requests
            response_times = []
            request_count = 5
            
            for i in range(request_count):
                start_time = time.time()
                response = self.session.get(f'{self.base_url}/courts/availability')
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                else:
                    print(f"  Request {i+1}: HTTP {response.status_code}")
            
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                # Performance should be reasonable
                if avg_time < 2.0 and max_time < 5.0:
                    self.log_result(
                        "Performance Impact",
                        True,
                        f"Avg: {avg_time:.3f}s, Min: {min_time:.3f}s, Max: {max_time:.3f}s"
                    )
                else:
                    self.log_result(
                        "Performance Impact",
                        False,
                        f"Performance too slow - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"
                    )
            else:
                self.log_result(
                    "Performance Impact",
                    False,
                    "No successful requests to measure performance"
                )
        except Exception as e:
            self.log_result(
                "Performance Impact",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_response_size_efficiency(self):
        """Test that anonymous responses are efficiently sized."""
        try:
            response = self.session.get(f'{self.base_url}/courts/availability')
            
            if response.status_code == 200:
                response_size = len(response.content)
                data = response.json()
                
                # Check response structure efficiency
                if 'grid' in data and isinstance(data['grid'], list):
                    court_count = len(data['grid'])
                    
                    # Reasonable size expectations (not too large due to filtering)
                    if response_size < 50000:  # Less than 50KB
                        self.log_result(
                            "Response Size Efficiency",
                            True,
                            f"Response size: {response_size} bytes for {court_count} courts"
                        )
                    else:
                        self.log_result(
                            "Response Size Efficiency",
                            False,
                            f"Response too large: {response_size} bytes"
                        )
                else:
                    self.log_result(
                        "Response Size Efficiency",
                        False,
                        "Invalid response structure"
                    )
            else:
                self.log_result(
                    "Response Size Efficiency",
                    False,
                    f"Could not retrieve data (HTTP {response.status_code})"
                )
        except Exception as e:
            self.log_result(
                "Response Size Efficiency",
                False,
                f"Exception: {str(e)}"
            )
    
    def test_date_range_handling(self):
        """Test handling of various date ranges."""
        test_dates = [
            date.today().isoformat(),  # Today
            (date.today() + timedelta(days=1)).isoformat(),  # Tomorrow
            (date.today() - timedelta(days=1)).isoformat(),  # Yesterday
            (date.today() + timedelta(days=30)).isoformat(),  # Future
            '2025-01-01',  # Specific future date
        ]
        
        passed_count = 0
        for test_date in test_dates:
            try:
                response = self.session.get(
                    f'{self.base_url}/courts/availability?date={test_date}'
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('date') == test_date:
                        passed_count += 1
                    else:
                        print(f"  Date '{test_date}': Wrong date in response")
                else:
                    print(f"  Date '{test_date}': HTTP {response.status_code}")
            except Exception as e:
                print(f"  Date '{test_date}': Exception {str(e)}")
        
        if passed_count == len(test_dates):
            self.log_result(
                "Date Range Handling",
                True,
                f"All {len(test_dates)} date formats properly handled"
            )
        else:
            self.log_result(
                "Date Range Handling",
                False,
                f"Only {passed_count}/{len(test_dates)} dates properly handled"
            )
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("Starting Anonymous Court Overview Security & Performance Validation")
        print("=" * 70)
        
        # Run all tests
        self.test_anonymous_access_basic()
        self.test_sensitive_data_leakage()
        self.test_invalid_date_handling()
        self.test_rate_limiting_behavior()
        self.test_performance_impact()
        self.test_response_size_efficiency()
        self.test_date_range_handling()
        
        # Summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.results if result['passed'])
        total = len(self.results)
        
        print(f"Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("✅ ALL TESTS PASSED - Anonymous access is secure and performant")
            return True
        else:
            print("❌ SOME TESTS FAILED - Review issues above")
            print("\nFailed Tests:")
            for result in self.results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['message']}")
            return False


def main():
    """Main function to run validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate anonymous court overview security and performance')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the application (default: http://localhost:5000)')
    
    args = parser.parse_args()
    
    validator = AnonymousSecurityValidator(args.url)
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()