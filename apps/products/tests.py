"""
Tests for products app.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Product, Tag
from .factories import (
    ProductFactory, TagFactory, CategoryFactory,
    FeaturedProductFactory, DigitalProductFactory,
    OutOfStockProductFactory, LowStockProductFactory
)

User = get_user_model()


class ProductAPITestCase(APITestCase):
    """Test cases for Product API."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.category = CategoryFactory()
        self.tag1 = TagFactory(name='Electronics')
        self.tag2 = TagFactory(name='Gadgets')
        
        # Create test products
        self.product1 = ProductFactory(
            name='Test Product 1',
            price=Decimal('99.99'),
            category=self.category,
            created_by=self.admin_user
        )
        self.product1.tags.add(self.tag1, self.tag2)
        
        self.product2 = FeaturedProductFactory(
            name='Featured Product',
            price=Decimal('199.99'),
            created_by=self.admin_user
        )
        
        self.product3 = OutOfStockProductFactory(
            name='Out of Stock Product',
            created_by=self.admin_user
        )
    
    def test_list_products_anonymous(self):
        """Test that anonymous users can list active products."""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_products_with_filtering(self):
        """Test product filtering."""
        url = reverse('product-list')
        
        # Filter by category
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.product1.id)
        
        # Filter by price range
        response = self.client.get(url, {'price_min': 150})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.product2.id)
        
        # Filter featured products
        response = self.client.get(url, {'is_featured': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.product2.id)
    
    def test_search_products(self):
        """Test product search functionality."""
        url = reverse('product-search')
        
        # Search by name
        response = self.client.get(url, {'q': 'Test Product'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Search by tag
        response = self.client.get(url, {'q': 'Electronics'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_featured_products(self):
        """Test featured products endpoint."""
        url = reverse('product-featured')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.product2.id)
    
    def test_in_stock_products(self):
        """Test in stock products endpoint."""
        url = reverse('product-in-stock')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return products that are in stock (not the out of stock one)
        product_ids = [item['id'] for item in response.data['results']]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
        self.assertNotIn(self.product3.id, product_ids)
    
    def test_retrieve_product(self):
        """Test retrieving a single product."""
        url = reverse('product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product1.id)
        self.assertEqual(response.data['name'], self.product1.name)
        self.assertIn('tags', response.data)
        self.assertIn('category', response.data)
    
    def test_create_product_unauthorized(self):
        """Test that anonymous users cannot create products."""
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'price': '49.99',
            'category': self.category.id
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_product_authorized(self):
        """Test that admin users can create products."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'description': 'A new test product',
            'short_description': 'New product',
            'price': '49.99',
            'category': self.category.id,
            'tag_ids': [self.tag1.id]
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')
        
        # Verify product was created
        product = Product.objects.get(id=response.data['id'])
        self.assertEqual(product.name, 'New Product')
        self.assertEqual(product.created_by, self.admin_user)
        self.assertIn(self.tag1, product.tags.all())
    
    def test_update_product_stock(self):
        """Test updating product stock."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-update-stock', kwargs={'pk': self.product1.pk})
        data = {'quantity': 50}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_quantity'], 50)
        
        # Verify stock was updated
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock_quantity, 50)
    
    def test_update_product_stock_invalid_data(self):
        """Test updating product stock with invalid data."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-update-stock', kwargs={'pk': self.product1.pk})
        
        # Test negative quantity
        data = {'quantity': -5}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing quantity
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_product_validation(self):
        """Test product creation validation."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('product-list')
        
        # Test invalid price
        data = {
            'name': 'Invalid Product',
            'price': '-10.00',
            'category': self.category.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test compare price validation
        data = {
            'name': 'Invalid Product',
            'price': '100.00',
            'compare_price': '50.00',  # Should be higher than price
            'category': self.category.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TagAPITestCase(APITestCase):
    """Test cases for Tag API."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.tag1 = TagFactory(name='Test Tag 1')
        self.tag2 = TagFactory(name='Test Tag 2')
    
    def test_list_tags_anonymous(self):
        """Test that anonymous users can list tags."""
        url = reverse('tag-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_tag_unauthorized(self):
        """Test that anonymous users cannot create tags."""
        url = reverse('tag-list')
        data = {'name': 'New Tag', 'color': '#FF0000'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_tag_authorized(self):
        """Test that admin users can create tags."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('tag-list')
        data = {'name': 'New Tag', 'color': '#FF0000'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Tag')


@pytest.mark.django_db
class ProductModelTestCase:
    """Test cases for Product model."""
    
    def test_product_str(self):
        """Test product string representation."""
        product = ProductFactory(name='Test Product')
        assert str(product) == 'Test Product'
    
    def test_product_slug_generation(self):
        """Test that slug is generated from name."""
        product = ProductFactory(name='Test Product Name')
        assert product.slug == 'test-product-name'
    
    def test_product_sku_generation(self):
        """Test that SKU is auto-generated."""
        product = ProductFactory()
        assert product.sku is not None
        assert product.sku.startswith('SKU')
    
    def test_is_in_stock_property(self):
        """Test is_in_stock property."""
        # Product with inventory tracking and stock
        product1 = ProductFactory(track_inventory=True, stock_quantity=10)
        assert product1.is_in_stock is True
        
        # Product with inventory tracking but no stock
        product2 = ProductFactory(track_inventory=True, stock_quantity=0)
        assert product2.is_in_stock is False
        
        # Digital product (no inventory tracking)
        product3 = DigitalProductFactory()
        assert product3.is_in_stock is True
    
    def test_is_low_stock_property(self):
        """Test is_low_stock property."""
        # Product with normal stock
        product1 = ProductFactory(
            track_inventory=True, 
            stock_quantity=10, 
            low_stock_threshold=5
        )
        assert product1.is_low_stock is False
        
        # Product with low stock
        product2 = LowStockProductFactory()
        assert product2.is_low_stock is True
        
        # Digital product
        product3 = DigitalProductFactory()
        assert product3.is_low_stock is False
    
    def test_discount_percentage_property(self):
        """Test discount percentage calculation."""
        product = ProductFactory(price=Decimal('100.00'), compare_price=Decimal('120.00'))
        assert product.discount_percentage == 17  # (120-100)/120 * 100 = 16.67 rounded to 17


@pytest.mark.django_db  
class TagModelTestCase:
    """Test cases for Tag model."""
    
    def test_tag_str(self):
        """Test tag string representation."""
        tag = TagFactory(name='Test Tag')
        assert str(tag) == 'Test Tag'
    
    def test_tag_slug_generation(self):
        """Test that slug is generated from name."""
        tag = TagFactory(name='Test Tag Name')
        assert tag.slug == 'test-tag-name'
