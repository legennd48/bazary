#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.testing')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import Client
from django.test import TestCase

# Create a test client
client = Client()

print("Testing URL resolution...")

# Try different URL names that might exist
url_names = ['tag-list', 'tags-list', 'product-tag-list']

for name in url_names:
    try:
        url = reverse(name)
        print(f'{name}: {url}')
        
        # Test the actual endpoint
        response = client.get(url)
        print(f'  Status: {response.status_code}')
        if response.status_code == 404:
            print(f'  404 - Not found')
        elif response.status_code == 500:
            print(f'  500 - Server error')
        
    except NoReverseMatch as e:
        print(f'{name}: NoReverseMatch - {e}')

print("\nTesting direct URLs...")
direct_urls = ['/api/products/tags/', '/api/products/tags', '/api/tags/', '/api/tags']

for url in direct_urls:
    response = client.get(url)
    print(f'{url}: {response.status_code}')
