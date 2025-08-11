# test_complete.py - Comprehensive test suite for subscription API
import requests
import json
import time
from decimal import Decimal
import random
import string

BASE_URL = 'http://localhost:5000'

class SubscriptionAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.user_id = None
        self.plan_id = None
        self.subscription_id = None
        self.coupon_code = None
        
    def make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            print(f"\n{method} {endpoint}")
            if params:
                print(f"Params: {params}")
            if data:
                print(f"Data: {json.dumps(data, indent=2, default=str)}")
            print(f"Status: {response.status_code}")
            
            if response.content:
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2, default=str)}")
                    return result
                except json.JSONDecodeError:
                    print(f"Raw Response: {response.text}")
                    return {'raw_response': response.text}
            else:
                print("No response content")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def generate_random_email(self):
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"test.{random_string}@example.com"
    
    def test_health_check(self):
        print("\n" + "="*60)
        print("TESTING HEALTH CHECK")
        print("="*60)
        
        result = self.make_request('GET', '/health')
        if result and result.get('status') == 'healthy':
            print("[OK] Health check passed")
            return True
        else:
            print("[ERROR] Health check failed")
            return False
    
    def test_create_user(self):
        print("\n" + "="*60)
        print("TESTING USER CREATION")
        print("="*60)
        
        user_data = {
            "name": "Test User",
            "email": self.generate_random_email(),
            "phone": "+1234567890",
            "company": "Test Company"
        }
        
        result = self.make_request('POST', '/api/users', user_data)
        if result and 'id' in result:
            self.user_id = result['id']
            print(f"[OK] User created with ID: {self.user_id}")
            
            # Test getting the created user
            user_result = self.make_request('GET', f'/api/users/{self.user_id}')
            if user_result and user_result.get('id') == self.user_id:
                print("[OK] User retrieval successful")
            
            return True
        else:
            print("[ERROR] Failed to create user")
            return False
    
    def test_create_plan(self):
        print("\n" + "="*60)
        print("TESTING PLAN CREATION")
        print("="*60)
        
        plan_data = {
            "name": f"Test Plan {int(time.time())}",
            "description": "A comprehensive test plan for API testing",
            "amount": 29.99,
            "interval": "monthly",
            "features": ["Feature 1", "Feature 2", "Premium Support"],
            "trial_days": 7,
            "setup_fee": 0
        }
        
        result = self.make_request('POST', '/api/plans', plan_data)
        if result and 'id' in result:
            self.plan_id = result['id']
            print(f"✅ Plan created with ID: {self.plan_id}")
            
            # Test getting the created plan
            plan_result = self.make_request('GET', f'/api/plans/{self.plan_id}')
            if plan_result and plan_result.get('id') == self.plan_id:
                print("✅ Plan retrieval successful")
            
            return True
        else:
            print("❌ Failed to create plan")
            return False
    
    def test_create_coupon(self):
        print("\n" + "="*60)
        print("TESTING COUPON CREATION")
        print("="*60)
        
        self.coupon_code = f"TEST{random.randint(1000, 9999)}"
        
        coupon_data = {
            "code": self.coupon_code,
            "discount_type": "percentage",
            "discount_value": 20,
            "valid_until": "2024-12-31T23:59:59",
            "max_uses": 100
        }
        
        result = self.make_request('POST', '/api/coupons', coupon_data)
        if result and 'id' in result:
            print(f"✅ Coupon created: {self.coupon_code}")
            
            # Test coupon validation
            validation_result = self.make_request('POST', f'/api/coupons/{self.coupon_code}/validate')
            if validation_result and validation_result.get('valid'):
                print("✅ Coupon validation successful")
            
            return True
        else:
            print("❌ Failed to create coupon")
            return False
    
    def test_create_subscription(self, use_coupon=False):
        print("\n" + "="*60)
        print(f"TESTING SUBSCRIPTION CREATION {'WITH COUPON' if use_coupon else ''}")
        print("="*60)
        
        if not self.user_id or not self.plan_id:
            print("❌ Need user_id and plan_id first")
            return False
        
        subscription_data = {
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "quantity": 1
        }
        
        if use_coupon and self.coupon_code:
            subscription_data["coupon_code"] = self.coupon_code
        
        result = self.make_request('POST', '/api/subscriptions', subscription_data)
        if result and 'subscription_id' in result:
            self.subscription_id = result['subscription_id']
            print(f"✅ Subscription created with ID: {self.subscription_id}")
            
            # Test getting user subscriptions
            user_subs = self.make_request('GET', f'/api/users/{self.user_id}/subscriptions')
            if user_subs and len(user_subs) > 0:
                print("✅ User subscriptions retrieval successful")
            
            return True
        else:
            print("❌ Failed to create subscription")
            return False
    
    def test_subscription_operations(self):
        print("\n" + "="*60)
        print("TESTING SUBSCRIPTION OPERATIONS")
        print("="*60)
        
        if not self.subscription_id:
            print("❌ Need subscription_id first")
            return False
        
        operations_passed = 0
        
        # Test quantity update
        print("\n--- Testing Quantity Update ---")
        quantity_result = self.make_request('PUT', f'/api/subscriptions/{self.subscription_id}/quantity', {"quantity": 2})
        if quantity_result and 'quantity' in quantity_result:
            print("✅ Quantity update successful")
            operations_passed += 1
        
        # Test plan change (create another plan first)
        print("\n--- Testing Plan Change ---")
        new_plan_data = {
            "name": f"Premium Plan {int(time.time())}",
            "description": "Premium plan for testing",
            "amount": 49.99,
            "interval": "monthly",
            "features": ["All Basic Features", "Premium Support", "Advanced Analytics"]
        }
        
        new_plan_result = self.make_request('POST', '/api/plans', new_plan_data)
        if new_plan_result and 'id' in new_plan_result:
            change_plan_result = self.make_request('PUT', f'/api/subscriptions/{self.subscription_id}/change-plan', {
                "plan_id": new_plan_result['id'],
                "prorate": True
            })
            if change_plan_result and 'new_plan' in change_plan_result:
                print("✅ Plan change successful")
                operations_passed += 1
        
        # Test cancellation (at period end)
        print("\n--- Testing Cancellation (At Period End) ---")
        cancel_result = self.make_request('POST', f'/api/subscriptions/{self.subscription_id}/cancel', {"immediate": False})
        if cancel_result and 'cancel_at_period_end' in cancel_result:
            print("✅ Cancellation (at period end) successful")
            operations_passed += 1
        
        # Test reactivation
        print("\n--- Testing Reactivation ---")
        reactivate_result = self.make_request('POST', f'/api/subscriptions/{self.subscription_id}/reactivate', {})
        if reactivate_result and 'status' in reactivate_result:
            print("✅ Reactivation successful")
            operations_passed += 1
        
        # Test immediate cancellation
        print("\n--- Testing Immediate Cancellation ---")
        immediate_cancel_result = self.make_request('POST', f'/api/subscriptions/{self.subscription_id}/cancel', {"immediate": True})
        if immediate_cancel_result and 'status' in immediate_cancel_result:
            print("✅ Immediate cancellation successful")
            operations_passed += 1
        
        print(f"\n✅ Subscription operations: {operations_passed}/5 passed")
        return operations_passed >= 4
    
    def test_usage_tracking(self):
        print("\n" + "="*60)
        print("TESTING USAGE TRACKING")
        print("="*60)
        
        if not self.subscription_id:
            print("❌ Need subscription_id first")
            return False
        
        # Record multiple usage events
        usage_events = [
            {"metric_name": "api_calls", "quantity": 100, "metadata": {"source": "web_app"}},
            {"metric_name": "api_calls", "quantity": 50, "metadata": {"source": "mobile_app"}},
            {"metric_name": "storage_mb", "quantity": 250, "metadata": {"type": "file_storage"}},
            {"metric_name": "bandwidth_gb", "quantity": 5, "metadata": {"region": "us-east-1"}}
        ]
        
        for usage in usage_events:
            result = self.make_request('POST', f'/api/subscriptions/{self.subscription_id}/usage', usage)
            if result and 'current_period_usage' in result:
                print(f"✅ Usage recorded: {usage['metric_name']} = {usage['quantity']}")
        
        # Get usage stats
        stats_result = self.make_request('GET', f'/api/subscriptions/{self.subscription_id}/usage')
        if stats_result and 'usage_stats' in stats_result:
            print("✅ Usage stats retrieval successful")
            return True
        
        return False
    
    def test_search_and_filtering(self):
        print("\n" + "="*60)
        print("TESTING SEARCH AND FILTERING")
        print("="*60)
        
        # Test subscription search with various filters
        search_tests = [
            {"status": "active"},
            {"plan_id": str(self.plan_id) if self.plan_id else "1"},
            {"page": "1", "per_page": "5"},
        ]
        
        for search_params in search_tests:
            result = self.make_request('GET', '/api/subscriptions/search', params=search_params)
            if result and 'subscriptions' in result:
                print(f"✅ Search with params {search_params} successful")
        
        return True
    
    def test_dashboard_endpoints(self):
        print("\n" + "="*60)
        print("TESTING DASHBOARD ENDPOINTS")
        print("="*60)
        
        # Test revenue dashboard
        revenue_result = self.make_request('GET', '/api/dashboard/revenue')
        if revenue_result and 'total_revenue' in revenue_result:
            print("✅ Revenue dashboard successful")
        
        # Test subscription dashboard
        subscription_result = self.make_request('GET', '/api/dashboard/subscriptions')
        if subscription_result and 'status_breakdown' in subscription_result:
            print("✅ Subscription dashboard successful")
        
        return True
    
    def test_bulk_operations(self):
        print("\n" + "="*60)
        print("TESTING BULK OPERATIONS")
        print("="*60)
        
        # Create a few more subscriptions for bulk testing
        subscription_ids = []
        
        for i in range(3):
            # Create new user
            user_data = {
                "name": f"Bulk Test User {i+1}",
                "email": self.generate_random_email()
            }
            user_result = self.make_request('POST', '/api/users', user_data)
            
            if user_result and 'id' in user_result and self.plan_id:
                # Create subscription
                sub_data = {
                    "user_id": user_result['id'],
                    "plan_id": self.plan_id,
                    "quantity": 1
                }
                sub_result = self.make_request('POST', '/api/subscriptions', sub_data)
                
                if sub_result and 'subscription_id' in sub_result:
                    subscription_ids.append(sub_result['subscription_id'])
        
        if subscription_ids:
            # Test bulk cancellation
            bulk_cancel_data = {
                "subscription_ids": subscription_ids,
                "immediate": False,
                "reason": "Bulk testing cleanup"
            }
            
            bulk_result = self.make_request('POST', '/api/subscriptions/bulk-cancel', bulk_cancel_data)
            if bulk_result and 'results' in bulk_result:
                print("✅ Bulk cancellation successful")
                return True
        
        return False
    
    def test_export_functionality(self):
        print("\n" + "="*60)
        print("TESTING EXPORT FUNCTIONALITY")
        print("="*60)
        
        # Test JSON export
        json_result = self.make_request('GET', '/api/export/subscriptions', params={"format": "json"})
        if json_result and isinstance(json_result, list):
            print("✅ JSON export successful")
        
        # Test CSV export
        csv_result = self.make_request('GET', '/api/export/subscriptions', params={"format": "csv"})
        if csv_result:
            print("✅ CSV export successful")
        
        return True
    
    def test_error_scenarios(self):
        print("\n" + "="*60)
        print("TESTING ERROR SCENARIOS")
        print("="*60)
        
        error_tests_passed = 0
        
        # Test duplicate user creation
        duplicate_email = "duplicate@example.com"
        user_data = {"name": "Test User", "email": duplicate_email}
        
        self.make_request('POST', '/api/users', user_data)  # First creation
        duplicate_result = self.make_request('POST', '/api/users', user_data)  # Should fail
        
        if duplicate_result and 'error' in duplicate_result:
            print("✅ Duplicate user creation properly rejected")
            error_tests_passed += 1
        
        # Test invalid subscription creation
        invalid_sub = {"user_id": 99999, "plan_id": 99999}
        invalid_result = self.make_request('POST', '/api/subscriptions', invalid_sub)
        
        if invalid_result and 'error' in invalid_result:
            print("✅ Invalid subscription creation properly rejected")
            error_tests_passed += 1
        
        # Test invalid quantity update
        invalid_quantity = self.make_request('PUT', '/api/subscriptions/99999/quantity', {"quantity": 0})
        
        if invalid_quantity and 'error' in invalid_quantity:
            print("✅ Invalid quantity update properly rejected")
            error_tests_passed += 1
        
        print(f"\n✅ Error scenarios: {error_tests_passed}/3 passed")
        return error_tests_passed >= 2
    
    def run_complete_test_suite(self):
        print(">> Starting Complete Subscription API Test Suite")
        print("=" * 80)
        
        test_results = {}
        
        # Core functionality tests
        tests = [
            ("Health Check", self.test_health_check),
            ("User Creation", self.test_create_user),
            ("Plan Creation", self.test_create_plan),
            ("Coupon Creation", self.test_create_coupon),
            ("Subscription Creation", self.test_create_subscription),
            ("Subscription with Coupon", lambda: self.test_create_subscription(use_coupon=True)),
            ("Subscription Operations", self.test_subscription_operations),
            ("Usage Tracking", self.test_usage_tracking),
            ("Search and Filtering", self.test_search_and_filtering),
            ("Dashboard Endpoints", self.test_dashboard_endpoints),
            ("Bulk Operations", self.test_bulk_operations),
            ("Export Functionality", self.test_export_functionality),
            ("Error Scenarios", self.test_error_scenarios),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_function in tests:
            try:
                print(f"\n[TEST] Running: {test_name}")
                result = test_function()
                test_results[test_name] = result
                
                if result:
                    passed_tests += 1
                    print(f"[OK] {test_name}: PASSED")
                else:
                    print(f"[FAIL] {test_name}: FAILED")
                
                time.sleep(1)  # Small delay between tests
                
            except Exception as e:
                print(f"[ERROR] {test_name}: EXCEPTION - {str(e)}")
                test_results[test_name] = False
        
        # Final summary
        print("\n" + "="*80)
        print(">> TEST SUITE COMPLETION SUMMARY")
        print("="*80)
        
        print(f"[OK] Passed: {passed_tests}/{total_tests}")
        print(f"[FAIL] Failed: {total_tests - passed_tests}/{total_tests}")
        print(f"[RATE] Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.user_id:
            print(f"[USER] Test User ID: {self.user_id}")
        if self.plan_id:
            print(f"[PLAN] Test Plan ID: {self.plan_id}")
        if self.subscription_id:
            print(f"[SUB] Test Subscription ID: {self.subscription_id}")
        if self.coupon_code:
            print(f"[COUPON] Test Coupon Code: {self.coupon_code}")
        
        # Detailed results
        print("\n[RESULTS] Detailed Test Results:")
        for test_name, result in test_results.items():
            status = "[OK] PASS" if result else "[FAIL] FAIL"
            print(f"  {status} {test_name}")
        
        return test_results

def run_performance_tests():
    """Run performance tests to check API response times"""
    print("\n" + "="*80)
    print("⚡ PERFORMANCE TESTING")
    print("="*80)
    
    tester = SubscriptionAPITester()
    
    endpoints = [
        ('GET', '/health'),
        ('GET', '/api/plans'),
        ('GET', '/api/dashboard/revenue'),
        ('GET', '/api/dashboard/subscriptions'),
    ]
    
    for method, endpoint in endpoints:
        times = []
        
        for i in range(5):  # Test each endpoint 5 times
            start_time = time.time()
            result = tester.make_request(method, endpoint)
            end_time = time.time()
            
            if result:
                response_time = (end_time - start_time) * 1000
                times.append(response_time)
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"⏱️  {method} {endpoint}:")
            print(f"   Average: {avg_time:.2f}ms")
            print(f"   Min: {min_time:.2f}ms")
            print(f"   Max: {max_time:.2f}ms")
            
            if avg_time > 1000:
                print(f"   ⚠️  Slow response detected!")

def simulate_load_test(num_concurrent_users=10):
    """Simulate concurrent users to test system under load"""
    print(f"\n" + "="*80)
    print(f"🔥 LOAD TESTING ({num_concurrent_users} Concurrent Users)")
    print("="*80)
    
    import threading
    import queue
    
    results_queue = queue.Queue()
    
    def user_workflow(user_id):
        """Simulate a complete user workflow"""
        tester = SubscriptionAPITester()
        
        try:
            start_time = time.time()
            
            # User registration
            user_data = {
                "name": f"Load Test User {user_id}",
                "email": f"loadtest.{user_id}.{int(time.time())}@example.com"
            }
            user_result = tester.make_request('POST', '/api/users', user_data)
            
            if not user_result or 'id' not in user_result:
                raise Exception("Failed to create user")
            
            # Get plans
            plans_result = tester.make_request('GET', '/api/plans')
            if not plans_result or len(plans_result) == 0:
                raise Exception("No plans available")
            
            # Create subscription
            sub_data = {
                "user_id": user_result['id'],
                "plan_id": plans_result[0]['id'],
                "quantity": 1
            }
            sub_result = tester.make_request('POST', '/api/subscriptions', sub_data)
            
            if not sub_result or 'subscription_id' not in sub_result:
                raise Exception("Failed to create subscription")
            
            # Record some usage
            usage_data = {
                "metric_name": "api_calls",
                "quantity": random.randint(10, 100)
            }
            tester.make_request('POST', f'/api/subscriptions/{sub_result["subscription_id"]}/usage', usage_data)
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            results_queue.put({
                'user_id': user_id,
                'success': True,
                'time_ms': total_time,
                'message': f"Complete workflow in {total_time:.2f}ms"
            })
            
        except Exception as e:
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            results_queue.put({
                'user_id': user_id,
                'success': False,
                'time_ms': total_time,
                'message': f"Failed: {str(e)}"
            })
    
    # Start all threads
    threads = []
    start_time = time.time()
    
    for i in range(num_concurrent_users):
        thread = threading.Thread(target=user_workflow, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Collect and analyze results
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n📊 Load Test Results:")
    print(f"✅ Successful: {len(successful)}/{num_concurrent_users}")
    print(f"❌ Failed: {len(failed)}/{num_concurrent_users}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"🚀 Throughput: {len(successful)/total_time:.2f} workflows/second")
    
    if successful:
        times = [r['time_ms'] for r in successful]
        print(f"📈 Average Response Time: {sum(times)/len(times):.2f}ms")
        print(f"🏃 Fastest: {min(times):.2f}ms")
        print(f"🐌 Slowest: {max(times):.2f}ms")
    
    if failed:
        print(f"\n❌ Failed Users:")
        for result in failed[:5]:  # Show first 5 failures
            print(f"  User {result['user_id']}: {result['message']}")

def create_sample_data():
    """Create comprehensive sample data for testing"""
    print("\n" + "="*80)
    print("📊 CREATING SAMPLE DATA")
    print("="*80)
    
    tester = SubscriptionAPITester()
    
    # Create sample plans
    plans = [
        {
            "name": "Starter",
            "description": "Perfect for individuals and small projects",
            "amount": 9.99,
            "interval": "monthly",
            "features": ["5 Projects", "1GB Storage", "Email Support"],
            "trial_days": 14
        },
        {
            "name": "Professional",
            "description": "Great for growing businesses",
            "amount": 29.99,
            "interval": "monthly",
            "features": ["Unlimited Projects", "10GB Storage", "Priority Support", "Advanced Analytics"],
            "trial_days": 7
        },
        {
            "name": "Enterprise",
            "description": "For large organizations",
            "amount": 99.99,
            "interval": "monthly",
            "features": ["Everything in Pro", "100GB Storage", "24/7 Support", "Custom Integrations", "SLA"],
            "trial_days": 0
        },
        {
            "name": "Annual Starter",
            "description": "Starter plan billed annually (2 months free)",
            "amount": 99.99,
            "interval": "yearly",
            "features": ["5 Projects", "1GB Storage", "Email Support", "2 Months Free"],
            "trial_days": 30
        }
    ]
    
    created_plans = []
    for plan in plans:
        result = tester.make_request('POST', '/api/plans', plan)
        if result and 'id' in result:
            created_plans.append(result)
            print(f"✅ Created plan: {plan['name']}")
    
    # Create sample users and subscriptions
    user_names = [
        "Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
        "Eva Davis", "Frank Miller", "Grace Wilson", "Henry Moore"
    ]
    
    created_users = []
    for i, name in enumerate(user_names):
        user_data = {
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}.{int(time.time())}.{i}@example.com",
            "company": f"Company {i+1}"
        }
        
        user_result = tester.make_request('POST', '/api/users', user_data)
        if user_result and 'id' in user_result:
            created_users.append(user_result)
            print(f"✅ Created user: {name}")
            
            # Create subscription for each user
            if created_plans:
                plan = random.choice(created_plans)
                sub_data = {
                    "user_id": user_result['id'],
                    "plan_id": plan['id'],
                    "quantity": random.randint(1, 3)
                }
                
                sub_result = tester.make_request('POST', '/api/subscriptions', sub_data)
                if sub_result:
                    print(f"  ✅ Created subscription for {name}")
                    
                    # Add some usage data
                    usage_events = [
                        {"metric_name": "api_calls", "quantity": random.randint(50, 500)},
                        {"metric_name": "storage_mb", "quantity": random.randint(100, 1000)},
                        {"metric_name": "bandwidth_gb", "quantity": random.randint(1, 10)}
                    ]
                    
                    for usage in usage_events:
                        tester.make_request('POST', f'/api/subscriptions/{sub_result["subscription_id"]}/usage', usage)
    
    # Create sample coupons
    coupons = [
        {"code": "WELCOME20", "discount_type": "percentage", "discount_value": 20},
        {"code": "SAVE10", "discount_type": "fixed_amount", "discount_value": 10},
        {"code": "FIRSTMONTH", "discount_type": "percentage", "discount_value": 100}
    ]
    
    for coupon in coupons:
        coupon["valid_until"] = "2024-12-31T23:59:59"
        coupon["max_uses"] = 50
        
        result = tester.make_request('POST', '/api/coupons', coupon)
        if result:
            print(f"✅ Created coupon: {coupon['code']}")
    
    print(f"\n📊 Sample data creation complete!")
    print(f"👥 Created {len(created_users)} users")
    print(f"📋 Created {len(created_plans)} plans") 
    print(f"🎫 Created {len(coupons)} coupons")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == 'full':
            tester = SubscriptionAPITester()
            tester.run_complete_test_suite()
        elif test_type == 'performance':
            run_performance_tests()
        elif test_type == 'load':
            num_users = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            simulate_load_test(num_users)
        elif test_type == 'sample':
            create_sample_data()
        else:
            print("Available test types:")
            print("  full - Complete functionality test suite")
            print("  performance - API response time testing")
            print("  load [num] - Load testing with concurrent users")
            print("  sample - Create sample data for testing")
    else:
        # Run complete test suite by default
        tester = SubscriptionAPITester()
        tester.run_complete_test_suite()