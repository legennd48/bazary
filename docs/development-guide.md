# 🛠️ Development Guide

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **PostgreSQL** (if running locally)
- **Redis** (optional, for caching)

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/legennd48/bazary.git
cd bazary

# 2. Copy environment variables
cp .env.example .env.dev

# 3. Start development environment
docker-compose up --build

# 4. Open new terminal and run migrations
docker-compose exec web python manage.py migrate

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser

# 6. Load sample data (optional)
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

### Access Points

- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Swagger Docs**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

## 🔧 Environment Configuration

### Environment Variables

```bash
# .env.dev
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key-change-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://bazary_user:bazary_pass@db:5432/bazary_dev
POSTGRES_DB=bazary_dev
POSTGRES_USER=bazary_user
POSTGRES_PASSWORD=bazary_pass

# Redis
REDIS_URL=redis://redis:6379/0

# Email (development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15
JWT_REFRESH_TOKEN_LIFETIME=7
```

### Settings Structure

```python
# bazary/settings/
├── __init__.py
├── base.py          # Common settings
├── development.py   # Development overrides
├── testing.py       # Test configuration
├── staging.py       # Staging environment
└── production.py    # Production settings
```

## 📁 Project Structure

```
bazary/
├── bazary/                 # Main Django project
│   ├── __init__.py
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # Main URL configuration
│   ├── wsgi.py          # WSGI application
│   └── asgi.py          # ASGI application
├── apps/                 # Django applications
│   ├── authentication/  # User authentication
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── products/        # Product management
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── categories/      # Category management
│   └── core/           # Shared utilities
│       ├── permissions.py
│       ├── pagination.py
│       ├── exceptions.py
│       └── utils.py
├── static/             # Static files
├── media/              # User uploads
├── templates/          # Django templates
├── fixtures/           # Sample data
├── tests/              # Project-wide tests
├── docs/               # Documentation
├── requirements/       # Environment requirements
├── docker/             # Docker configurations
├── scripts/            # Utility scripts
└── manage.py
```

## 🧪 Development Workflow

### 1. Git Flow Setup

```bash
# Install git-flow
# Ubuntu/Debian
sudo apt-get install git-flow

# macOS
brew install git-flow-avh

# Initialize git flow
git flow init

# Start new feature
git flow feature start feature-name

# Finish feature
git flow feature finish feature-name
```

### 2. Code Quality Tools

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

#### Code Formatting

```bash
# Format code
black .

# Check formatting
black --check .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking (optional)
mypy .
```

### 3. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest apps/products/tests/test_models.py

# Run specific test
pytest apps/products/tests/test_models.py::TestProductModel::test_create_product

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### 4. Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create migration for specific app
python manage.py makemigrations products

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate products 0001

# SQL for migration
python manage.py sqlmigrate products 0001
```

## 🎯 Coding Standards

### Python Code Style

We follow **PEP 8** with some modifications:

```python
# Line length: 88 characters (Black default)
# Use double quotes for strings
# Use trailing commas in multi-line structures

# Good example
class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with custom validation."""
    
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )
    
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "category_name",
            "in_stock",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )
        return value
```

### Django Best Practices

#### Models

```python
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel

class Product(TimeStampedModel):
    """Product model with validation and methods."""
    
    name = models.CharField(
        max_length=255,
        help_text="Product name (max 255 characters)"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed product description"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Product price in USD"
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        related_name="products"
    )
    in_stock = models.BooleanField(
        default=True,
        help_text="Whether product is currently available"
    )
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category", "in_stock"]),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_expensive(self):
        """Check if product is expensive (>$100)."""
        return self.price > 100
```

#### Views

```python
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.pagination import StandardResultsSetPagination

class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    
    - GET: List products with filtering and pagination
    - POST: Create new product (admin only)
    """
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "in_stock"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Optimize database queries."""
        return Product.objects.select_related("category").filter(
            is_active=True
        )
    
    def perform_create(self, serializer):
        """Set created_by when creating product."""
        serializer.save(created_by=self.request.user)
```

#### URLs

```python
# apps/products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "products"

# Using ViewSets with Router
router = DefaultRouter()
router.register("", views.ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]

# Or using individual views
urlpatterns = [
    path("", views.ProductListCreateView.as_view(), name="product-list"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
]
```

## 📝 Testing Guidelines

### Test Structure

```python
# apps/products/tests/test_models.py
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.products.models import Product
from apps.categories.tests.factories import CategoryFactory

@pytest.mark.django_db
class TestProductModel:
    """Test Product model functionality."""
    
    def test_create_product_success(self):
        """Test successful product creation."""
        category = CategoryFactory()
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("29.99"),
            category=category,
        )
        
        assert product.name == "Test Product"
        assert product.price == Decimal("29.99")
        assert product.in_stock is True
        assert str(product) == "Test Product"
    
    def test_product_price_validation(self):
        """Test that negative prices are invalid."""
        category = CategoryFactory()
        
        with pytest.raises(ValidationError):
            product = Product(
                name="Invalid Product",
                price=Decimal("-10.00"),
                category=category,
            )
            product.full_clean()
    
    def test_is_expensive_property(self):
        """Test is_expensive property."""
        category = CategoryFactory()
        
        cheap_product = Product.objects.create(
            name="Cheap Product",
            price=Decimal("50.00"),
            category=category,
        )
        expensive_product = Product.objects.create(
            name="Expensive Product",
            price=Decimal("150.00"),
            category=category,
        )
        
        assert not cheap_product.is_expensive
        assert expensive_product.is_expensive
```

### Factory Boy Usage

```python
# apps/products/tests/factories.py
import factory
from decimal import Decimal
from apps.products.models import Product
from apps.categories.tests.factories import CategoryFactory

class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for creating Product instances."""
    
    class Meta:
        model = Product
    
    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=500)
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=1,
        max_value=999,
    )
    category = factory.SubFactory(CategoryFactory)
    in_stock = True

# Usage in tests
def test_product_list_view():
    products = ProductFactory.create_batch(10)
    # Test logic here
```

### API Testing

```python
# apps/products/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.products.tests.factories import ProductFactory

User = get_user_model()

@pytest.mark.django_db
class TestProductAPI:
    """Test Product API endpoints."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
    
    def test_list_products_anonymous(self):
        """Test that anonymous users can list products."""
        ProductFactory.create_batch(3)
        
        response = self.client.get("/api/products/")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
    
    def test_create_product_admin(self):
        """Test that admin users can create products."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "name": "New Product",
            "description": "Product description",
            "price": "99.99",
            "category": CategoryFactory().id,
        }
        
        response = self.client.post("/api/products/", data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Product"
    
    def test_create_product_regular_user_forbidden(self):
        """Test that regular users cannot create products."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "name": "New Product",
            "price": "99.99",
        }
        
        response = self.client.post("/api/products/", data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
```

## 🔧 Useful Commands

### Django Management Commands

```bash
# Start development server
python manage.py runserver

# Create app
python manage.py startapp app_name

# Django shell
python manage.py shell

# Django shell with iPython
python manage.py shell_plus

# Clear cache
python manage.py clear_cache

# Collect static files
python manage.py collectstatic

# Create dummy data
python manage.py seed_data
```

### Docker Commands

```bash
# Build and start services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute commands in container
docker-compose exec web python manage.py shell

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose build web
```

### Debugging

```bash
# Django debug toolbar
# Add to INSTALLED_APPS in development.py
'debug_toolbar',

# Add to MIDDLEWARE
'debug_toolbar.middleware.DebugToolbarMiddleware',

# ipdb debugging
import ipdb; ipdb.set_trace()

# Print SQL queries
from django.db import connection
print(connection.queries)
```

## 📚 Learning Resources

### Django Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)

### Testing Resources
- [Pytest Django](https://pytest-django.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)

### Code Quality
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8](https://flake8.pycqa.org/)
- [Pre-commit](https://pre-commit.com/)

This development guide should help team members get started quickly and maintain consistent code quality throughout the project.
