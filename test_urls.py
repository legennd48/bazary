#!/usr/bin/env python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazary.settings.testing")
django.setup()

from django.test import Client
from django.urls import reverse

client = Client()

# Test different URLs
test_urls = [
    "/api/products/",
    "/api/products/tags/",
    "/api/products/tags",
]

for url in test_urls:
    try:
        response = client.get(url)
        print(f"{url}: Status {response.status_code}")
    except Exception as e:
        print(f"{url}: Error {e}")

# Test URL reverse
try:
    product_url = reverse("product-list")
    print(f"product-list reverses to: {product_url}")
except Exception as e:
    print(f"product-list reverse failed: {e}")

try:
    tag_url = reverse("tag-list")
    print(f"tag-list reverses to: {tag_url}")
except Exception as e:
    print(f"tag-list reverse failed: {e}")
