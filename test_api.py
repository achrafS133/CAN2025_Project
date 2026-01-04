#!/usr/bin/env python3
"""
CAN 2025 Guardian API - Test Suite
Tests all API endpoints and verifies functionality
"""

import requests
import json
import time
from typing import Optional

# Configuration
API_BASE = "http://localhost:8888/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.passed = 0
        self.failed = 0

    def print_test(self, name: str, status: bool, details: str = ""):
        """Print test result"""
        symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
        print(f"{symbol} {name}")
        if details:
            print(f"  {YELLOW}└─{RESET} {details}")

        if status:
            self.passed += 1
        else:
            self.failed += 1

    def test_health(self):
        """Test health check endpoint"""
        print(f"\n{BLUE}Testing Health Check{RESET}")
        print("-" * 50)

        try:
            response = requests.get("http://localhost:8888/health")
            success = response.status_code == 200
            self.print_test("Health check", success, f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Health check", False, str(e))

    def test_authentication(self):
        """Test authentication endpoints"""
        print(f"\n{BLUE}Testing Authentication{RESET}")
        print("-" * 50)

        # Test login
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={"username": USERNAME, "password": PASSWORD},
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.print_test("Login", True, f"Token received: {self.token[:20]}...")
            else:
                self.print_test("Login", False, f"Status: {response.status_code}")
                return
        except Exception as e:
            self.print_test("Login", False, str(e))
            return

        # Test get current user
        try:
            response = requests.get(
                f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {self.token}"}
            )
            success = response.status_code == 200
            user = response.json() if success else {}
            self.print_test(
                "Get current user", success, f"Username: {user.get('username')}"
            )
        except Exception as e:
            self.print_test("Get current user", False, str(e))

    def test_threats(self):
        """Test threat detection endpoints"""
        print(f"\n{BLUE}Testing Threat Detection{RESET}")
        print("-" * 50)

        # Test get history
        try:
            response = requests.get(
                f"{API_BASE}/threats/history?limit=10",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Get threat history", success, f"Total: {data.get('total', 0)}"
            )
        except Exception as e:
            self.print_test("Get threat history", False, str(e))

        # Test get stats
        try:
            response = requests.get(
                f"{API_BASE}/threats/stats",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Get threat stats",
                success,
                f"Total detections: {data.get('total_detections', 0)}",
            )
        except Exception as e:
            self.print_test("Get threat stats", False, str(e))

    def test_ai_chatbot(self):
        """Test AI chatbot endpoints"""
        print(f"\n{BLUE}Testing AI Chatbot{RESET}")
        print("-" * 50)

        # Test get models
        try:
            response = requests.get(
                f"{API_BASE}/ai/models",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            models = response.json() if success else []
            model_names = (
                [m["name"] for m in models] if isinstance(models, list) else []
            )
            self.print_test(
                "Get AI models", success, f"Available: {', '.join(model_names)}"
            )
        except Exception as e:
            self.print_test("Get AI models", False, str(e))

        # Test chat
        try:
            response = requests.post(
                f"{API_BASE}/ai/chat",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": "What are the main security concerns for CAN 2025?",
                    "model": "openai",
                },
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            response_text = data.get("response", "")[:50]
            self.print_test(
                "Send chat message", success, f"Response: {response_text}..."
            )
        except Exception as e:
            self.print_test("Send chat message", False, str(e))

    def test_analytics(self):
        """Test analytics endpoints"""
        print(f"\n{BLUE}Testing Analytics{RESET}")
        print("-" * 50)

        # Test dashboard stats
        try:
            response = requests.get(
                f"{API_BASE}/analytics/dashboard",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Get dashboard stats",
                success,
                f"Incidents: {data.get('total_incidents', 0)}, "
                f"Alerts: {data.get('active_alerts', 0)}",
            )
        except Exception as e:
            self.print_test("Get dashboard stats", False, str(e))

        # Test anomaly detection
        try:
            response = requests.get(
                f"{API_BASE}/analytics/anomalies?metric=threat_count&days=7",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Anomaly detection", success, f"Detected: {data.get('detected', 0)}"
            )
        except Exception as e:
            self.print_test("Anomaly detection", False, str(e))

    def test_streams(self):
        """Test video stream endpoints"""
        print(f"\n{BLUE}Testing Video Streams{RESET}")
        print("-" * 50)

        # Test list streams
        try:
            response = requests.get(
                f"{API_BASE}/streams", headers={"Authorization": f"Bearer {self.token}"}
            )
            success = response.status_code == 200
            streams = response.json() if success else []
            self.print_test(
                "List streams",
                success,
                f"Total streams: {len(streams) if isinstance(streams, list) else 0}",
            )
        except Exception as e:
            self.print_test("List streams", False, str(e))

    def test_alerts_and_costs(self):
        """Test alerts and cost tracking endpoints"""
        print(f"\n{BLUE}Testing Alerts & Cost Tracking{RESET}")
        print("-" * 50)

        # Test get cost stats
        try:
            response = requests.get(
                f"{API_BASE}/costs", headers={"Authorization": f"Bearer {self.token}"}
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Get cost stats",
                success,
                f"Daily: ${data.get('daily_cost', 0):.4f}, "
                f"Monthly: ${data.get('monthly_cost', 0):.2f}",
            )
        except Exception as e:
            self.print_test("Get cost stats", False, str(e))

        # Test budget status
        try:
            response = requests.get(
                f"{API_BASE}/costs/budget",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.print_test(
                "Get budget status",
                success,
                f"Monthly spent: ${data.get('monthly_spent', 0):.2f} / "
                f"${data.get('monthly_budget', 0):.2f}",
            )
        except Exception as e:
            self.print_test("Get budget status", False, str(e))

    def test_rate_limiting(self):
        """Test rate limiting"""
        print(f"\n{BLUE}Testing Rate Limiting{RESET}")
        print("-" * 50)

        try:
            # Make rapid requests to trigger rate limit
            responses = []
            for i in range(5):
                response = requests.get(
                    f"{API_BASE}/threats/history?limit=1",
                    headers={"Authorization": f"Bearer {self.token}"},
                )
                responses.append(response.status_code)

            # Check if we got rate limit headers
            last_response = requests.get(
                f"{API_BASE}/threats/history?limit=1",
                headers={"Authorization": f"Bearer {self.token}"},
            )

            has_rate_limit_headers = (
                "X-RateLimit-Remaining-Minute" in last_response.headers
            )
            self.print_test(
                "Rate limit headers present",
                has_rate_limit_headers,
                f"Remaining: {last_response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')}",
            )
        except Exception as e:
            self.print_test("Rate limiting", False, str(e))

    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}{'=' * 60}{RESET}")
        print(f"{BLUE}CAN 2025 Guardian API - Test Suite{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}")

        self.test_health()
        self.test_authentication()

        if self.token:
            self.test_threats()
            self.test_ai_chatbot()
            self.test_analytics()
            self.test_streams()
            self.test_alerts_and_costs()
            self.test_rate_limiting()
        else:
            print(f"\n{RED}Skipping authenticated tests (login failed){RESET}")

        # Print summary
        print(f"\n{BLUE}{'=' * 60}{RESET}")
        print(f"{BLUE}Test Summary{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}")
        print(f"{GREEN}Passed:{RESET} {self.passed}")
        print(f"{RED}Failed:{RESET} {self.failed}")
        print(f"Total: {self.passed + self.failed}")

        success_rate = (
            (self.passed / (self.passed + self.failed) * 100)
            if (self.passed + self.failed) > 0
            else 0
        )
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if self.failed == 0:
            print(f"\n{GREEN}✓ All tests passed!{RESET} 🎉")
        else:
            print(f"\n{RED}✗ Some tests failed.{RESET} Please check the API logs.")


if __name__ == "__main__":
    print(
        f"\n{YELLOW}Make sure the API server is running on http://localhost:8888{RESET}"
    )
    print(
        f"{YELLOW}Start it with: ./start_api.sh or uvicorn api.main:app --reload --port 8888{RESET}\n"
    )

    input("Press Enter to start tests...")

    tester = APITester()
    tester.run_all_tests()
