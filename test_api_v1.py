#!/usr/bin/env python3
"""
Bazary API V1.0 Assessment Script
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def test_endpoint(name, method, url, data=None, headers=None):
    """Test an API endpoint"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, verify=False)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, verify=False)

        status = "✅ PASS" if response.status_code < 400 else "❌ FAIL"
        print(f"{status} {name}: {response.status_code}")

        if response.status_code < 400:
            try:
                resp_data = response.json()
                if "results" in resp_data:
                    print(f"    📊 Results: {len(resp_data['results'])} items")
                elif "count" in resp_data:
                    print(f"    📊 Count: {resp_data['count']} items")
            except:
                print(f"    📄 Response length: {len(response.text)} chars")

        return response.status_code < 400
    except Exception as e:
        print(f"❌ FAIL {name}: Connection error - {str(e)}")
        return False


def main():
    print("🔍 Bazary API V1.0 Assessment")
    print("=" * 50)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print()

    # Core API Tests
    print("📋 Core API Endpoints:")
    test_endpoint("Health Check", "GET", f"{BASE_URL}/health/")
    test_endpoint("API Root", "GET", f"{API_BASE}/")
    test_endpoint("Swagger Docs", "GET", f"{BASE_URL}/swagger/")
    print()

    # Product API Tests
    print("🛍️ Product Management:")
    test_endpoint("List Products", "GET", f"{API_BASE}/products/")
    test_endpoint("Product Search", "GET", f"{API_BASE}/products/search/")
    test_endpoint("Featured Products", "GET", f"{API_BASE}/products/featured/")
    test_endpoint("In Stock Products", "GET", f"{API_BASE}/products/in_stock/")
    test_endpoint(
        "Product Testing Instructions",
        "GET",
        f"{API_BASE}/products/testing-instructions/",
    )
    print()

    # Categories & Tags
    print("📂 Categories & Tags:")
    test_endpoint("List Categories", "GET", f"{API_BASE}/categories/")
    test_endpoint("List Tags", "GET", f"{API_BASE}/tags/")
    print()

    # Authentication Tests
    print("🔐 Authentication:")
    test_endpoint(
        "Register User",
        "POST",
        f"{API_BASE}/auth/register/",
        {
            "email": "testuser@example.com",
            "username": "testuser_v1",
            "password": "testpass123456",
            "password_confirm": "testpass123456",
        },
    )
    test_endpoint(
        "Login User",
        "POST",
        f"{API_BASE}/auth/token/",
        {"email": "testuser@example.com", "password": "testpass123456"},
    )
    test_endpoint(
        "Auth Testing Instructions", "GET", f"{API_BASE}/auth/testing-instructions/"
    )
    print()

    print("✅ Assessment Complete!")


if __name__ == "__main__":
    main()
