#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.development')
django.setup()

from apps.products.models import Product
from apps.categories.models import Category

# Check Electronics category
try:
    elec = Category.objects.get(slug='electronics')
    print(f"✅ Electronics category found: {elec.name} (ID: {elec.id})")
    
    # Check products directly in Electronics
    direct_products = Product.objects.filter(category=elec)
    print(f"\n📦 Products directly in 'Electronics': {direct_products.count()}")
    
    # Check subcategories
    subcats = Category.objects.filter(parent=elec)
    print(f"\n📂 Subcategories under Electronics: {subcats.count()}")
    for cat in subcats:
        count = Product.objects.filter(category=cat).count()
        print(f"   - {cat.name} (slug: {cat.slug}): {count} products")
    
    # Check all products
    print(f"\n📊 Total products in database: {Product.objects.count()}")
    print(f"   - Active products: {Product.objects.filter(is_active=True).count()}")
    print(f"   - Inactive products: {Product.objects.filter(is_active=False).count()}")
    
    # Show what categories products ARE in
    print("\n🏷️ Products distribution by category:")
    for cat in Category.objects.all()[:15]:
        count = Product.objects.filter(category=cat).count()
        if count > 0:
            print(f"   - {cat.name} (slug: {cat.slug}): {count} products")
    
except Category.DoesNotExist:
    print("❌ Electronics category not found!")
