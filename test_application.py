#!/usr/bin/env python3
"""
Comprehensive Application Testing Script
Tests all API endpoints and functionality
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"

class ApplicationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_data = None
        self.test_results = []
        
    def log_result(self, test_name, success, message=""):
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
    def test_registration(self):
        """Test user registration"""
        try:
            user_data = {
                "name": "Test User",
                "email": "test@example.com",
                "password": "testpassword123",
                "gender": "other",
                "ethnicity": "south asian",
                "activity_level": "moderate",
                "family_history_diabetes": True
            }
            
            response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
            
            if response.status_code == 201:
                self.log_result("User Registration", True, "Registration successful")
                return True
            else:
                self.log_result("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_login(self):
        """Test user login"""
        try:
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_data = data.get("user")
                self.log_result("User Login", True, f"Login successful for user: {self.user_data.get('name')}")
                return True
            else:
                self.log_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("User Login", False, f"Exception: {str(e)}")
            return False
    
    def test_get_profile(self):
        """Test getting user profile"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Get Profile", True, f"Profile retrieved for: {data.get('user', {}).get('name')}")
                return True
            else:
                self.log_result("Get Profile", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Profile", False, f"Exception: {str(e)}")
            return False
    
    def test_add_measurement(self):
        """Test adding various measurements"""
        measurements = [
            {
                "measurement_type": "fasting_glucose",
                "value": 95.0,
                "timestamp": datetime.now().isoformat(),
                "meal_context": "fasting"
            },
            {
                "measurement_type": "postprandial_glucose",
                "value": 140.0,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "meal_context": "post_meal_2h"
            },
            {
                "measurement_type": "hba1c",
                "value": 6.2,
                "timestamp": datetime.now().isoformat()
            },
            {
                "measurement_type": "weight",
                "value": 70.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "measurement_type": "physical_activity",
                "value": 30.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "measurement_type": "sleep_hours",
                "value": 7.5,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        success_count = 0
        for i, measurement in enumerate(measurements):
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{self.base_url}/api/measurements", json=measurement, headers=headers)
                
                if response.status_code == 201:
                    success_count += 1
                    self.log_result(f"Add Measurement {i+1}", True, f"Added {measurement['measurement_type']}: {measurement['value']}")
                else:
                    self.log_result(f"Add Measurement {i+1}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Add Measurement {i+1}", False, f"Exception: {str(e)}")
        
        # Add more measurements for stability calculation
        for i in range(15):  # Add 15 more glucose measurements
            glucose_type = random.choice(["fasting_glucose", "postprandial_glucose", "random_glucose"])
            base_value = 90 if glucose_type == "fasting_glucose" else 130
            value = base_value + random.uniform(-10, 20)
            
            measurement = {
                "measurement_type": glucose_type,
                "value": round(value, 1),
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "meal_context": random.choice(["fasting", "pre_meal", "post_meal_2h"]) if glucose_type != "fasting_glucose" else "fasting"
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = requests.post(f"{self.base_url}/api/measurements", json=measurement, headers=headers)
                if response.status_code == 201:
                    success_count += 1
            except:
                pass
        
        self.log_result("Add Multiple Measurements", success_count >= 10, f"Successfully added {success_count} measurements")
        return success_count >= 10
    
    def test_get_measurements(self):
        """Test retrieving measurements"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/measurements?days=30", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                measurements = data if isinstance(data, list) else []
                self.log_result("Get Measurements", True, f"Retrieved {len(measurements)} measurements")
                return True
            else:
                self.log_result("Get Measurements", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Measurements", False, f"Exception: {str(e)}")
            return False
    
    def test_stability_calculation(self):
        """Test stability score calculation"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/measurements/stability", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("insufficient_data"):
                    self.log_result("Stability Calculation", True, "Insufficient data (expected for new user)")
                else:
                    stability = data.get("stability")
                    if stability:
                        score = stability.get("stability_score")
                        self.log_result("Stability Calculation", True, f"Stability score: {score}")
                    else:
                        self.log_result("Stability Calculation", False, "No stability data returned")
                return True
            else:
                self.log_result("Stability Calculation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Stability Calculation", False, f"Exception: {str(e)}")
            return False
    
    def test_recommendations(self):
        """Test recommendations engine"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/recommendations", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                if data.get("insufficient_data"):
                    self.log_result("Recommendations", True, "Insufficient data for recommendations (expected)")
                else:
                    self.log_result("Recommendations", True, f"Generated {len(recommendations)} recommendations")
                return True
            else:
                self.log_result("Recommendations", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Recommendations", False, f"Exception: {str(e)}")
            return False
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Check", True, f"Status: {data.get('status')}, WebSocket port: {data.get('websocket_port')}")
                return True
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🧪 Starting Comprehensive Application Testing")
        print("=" * 50)
        
        # Core functionality tests
        self.test_health_endpoint()
        self.test_registration()
        self.test_login()
        self.test_get_profile()
        self.test_add_measurement()
        self.test_get_measurements()
        self.test_stability_calculation()
        self.test_recommendations()
        
        # Generate summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = ApplicationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Application is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(tester.test_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to test_results.json")
