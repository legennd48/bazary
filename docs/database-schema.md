````markdown
# 📊 Database Schema & Data Models

**Last Updated:** August 10, 2025  
**Database:** PostgreSQL (Development: SQLite)  
**Django Version:** 5.0.14  

---

## 🎯 Schema Overview

Bazary uses PostgreSQL with Django ORM, designed for scalability and performance optimization. The schema supports a comprehensive e-commerce platform with user management, product catalog with variants, categories, shopping cart, and payment processing.

```sql
-- Core Tables Relationship
User (1) ────────────> (*) Product (created_by)
User (1) ────────────> (*) Cart
User (1) ────────────> (*) PaymentMethod
User (1) ────────────> (*) Transaction
Category (1) ────────> (*) Product  
Category (1) ────────> (*) Category (parent/child)
Product (1) ─────────> (*) ProductVariant
Product (1) ─────────> (*) ProductImage
Product (*) ─────────> (*) Tag (many-to-many)
ProductVariant (1) ──> (*) ProductVariantImage
Cart (1) ────────────> (*) CartItem
CartItem (*) ────────> (1) Product
CartItem (*) ────────> (1) ProductVariant (optional)
PaymentProvider (1) ─> (*) PaymentMethod
PaymentProvider (1) ─> (*) Transaction
```

---

## 🗂️ Data Models

### 1. User Model (Extended)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    """Extended user model with additional fields."""
    
    USER_ROLES = [
        ("customer", "Customer"),
        ("staff", "Staff"), 
        ("admin", "Admin"),
        ("super_admin", "Super Admin"),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        help_text="User's email address (used for login)"
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text="User's phone number"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether user has verified their email"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text="User's profile picture"
    )
    role = models.CharField(
        max_length=20, 
        choices=USER_ROLES, 
        default="customer", 
        help_text="User role"
    )
    is_email_verified = models.BooleanField(
        default=False, 
        help_text="Whether user email is verified"
    )
    failed_login_attempts = models.PositiveIntegerField(
        default=0, 
        help_text="Number of consecutive failed login attempts"
    )
    account_locked_until = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Account locked until this time"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_email_verified']),
        ]
```

**Related Models:**
- `UserProfile`: Extended profile information
- `UserAddress`: Shipping/billing addresses  
- `EmailVerificationToken`: Email verification tokens
- `PasswordResetToken`: Password reset tokens
- `UserActivity`: Activity audit trail

### 2. Category Model

```python
class Category(TimeStampedModel):
    """Product category model with hierarchy support."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (unique)"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly category identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    image = models.ImageField(
        upload_to='categories/',
        null=True,
        blank=True,
        help_text="Category image"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Parent category for hierarchy"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether category is active"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
```

### 3. Product Model

```python
from django.core.validators import MinValueValidator
from decimal import Decimal

class Product(TimeStampedModel):
    """Product model with comprehensive fields."""
    
    name = models.CharField(
        max_length=255,
        help_text="Product name"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly product identifier"
    )
    description = models.TextField(
        help_text="Detailed product description"
    )
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief product summary"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stock Keeping Unit"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Product price"
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price (for discounts)"
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price (admin only)"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="Product category"
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        help_text="Product tags for filtering"
    )
    
    # Inventory
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Low stock warning threshold"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether product is active"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether product is featured"
    )
    is_digital = models.BooleanField(
        default=False,
        help_text="Whether product is digital"
    )
    
    # SEO
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta title"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description"
    )
    
    # Timestamps
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
            # Composite indexes for filtering
            models.Index(fields=['category', 'price']),
            models.Index(fields=['is_active', 'stock_quantity']),
        ]
```

### 4. Product Variants System

#### VariantOption Model
```python
class VariantOption(TimeStampedModel):
    """Variant option types (e.g., Color, Size, Material)."""
    
    name = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Option name (e.g., 'Color', 'Size')"
    )
    display_name = models.CharField(
        max_length=100, 
        help_text="Display name for frontend"
    )
    display_type = models.CharField(
        max_length=20,
        choices=[
            ("dropdown", "Dropdown"),
            ("color", "Color Picker"),
            ("button", "Button Selection"),
            ("radio", "Radio Button"),
        ],
        default="dropdown",
    )
    is_required = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
```

#### VariantOptionValue Model
```python
class VariantOptionValue(TimeStampedModel):
    """Values for variant options (e.g., Red, Blue for Color)."""
    
    option = models.ForeignKey(
        VariantOption,
        on_delete=models.CASCADE,
        related_name="values"
    )
    value = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=7, blank=True, null=True)
    image = models.ImageField(upload_to="variant_values/", blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
```

#### ProductVariant Model
```python
class ProductVariant(TimeStampedModel):
    """Specific product variants with their own pricing and inventory."""
    
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="variants"
    )
    sku = models.CharField(max_length=100, unique=True)
    
    # Pricing (can override product pricing)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    compare_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    # Physical attributes
    weight = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    dimensions_length = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    dimensions_width = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    dimensions_height = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
```

### 5. Product Images Model

```python
class ProductImage(TimeStampedModel):
    """Product image model for multiple images per product."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/',
        help_text="Product image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary image"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    class Meta:
        db_table = 'product_images'
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]
```

### 6. Tag Model

```python
class Tag(TimeStampedModel):
    """Tag model for product categorization."""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag name"
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="URL-friendly tag identifier"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Tag color (hex code)"
    )
    
    class Meta:
        db_table = 'tags'
        ordering = ['name']
```

### 7. Payment System Models

#### PaymentProvider Model
```python
class PaymentProvider(TimeStampedModel):
    """Payment provider configuration model."""
    
    class ProviderType(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        CHAPA = "chapa", "Chapa"  # Ethiopian payment gateway
        # ... other providers
    
    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=20, choices=ProviderType.choices)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200)
    webhook_secret = models.CharField(max_length=200, blank=True)
    test_mode = models.BooleanField(default=True)
    supported_currencies = models.JSONField(default=list)
    configuration = models.JSONField(default=dict)
```

#### PaymentMethod Model
```python
class PaymentMethod(TimeStampedModel):
    """User payment method model."""
    
    class MethodType(models.TextChoices):
        CARD = "card", "Credit/Debit Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        DIGITAL_WALLET = "digital_wallet", "Digital Wallet"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_methods")
    provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=20, choices=MethodType.choices)
    name = models.CharField(max_length=100)
    # ... additional fields for payment method details
```

#### Transaction Model
```python
class Transaction(TimeStampedModel):
    """Payment transaction records."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    payment_provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    
    # Transaction details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # External references
    external_transaction_id = models.CharField(max_length=200, blank=True)
    external_reference = models.CharField(max_length=200, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
```

### 8. Shopping Cart Models

#### Cart Model
```python
class Cart(TimeStampedModel):
    """Shopping cart model."""
    
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ABANDONED = "abandoned", "Abandoned"
        CONVERTED = "converted", "Converted to Order"
        EXPIRED = "expired", "Expired"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    currency = models.CharField(max_length=3, default="USD")
    
    # Calculated pricing fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    
    # Cart metadata
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    expires_at = models.DateTimeField(null=True, blank=True)
```

#### CartItem Model
```python
class CartItem(TimeStampedModel):
    """Individual items in shopping cart."""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Price at time of adding to cart
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Item metadata
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
```

## 🔍 Database Indexes Strategy

### Primary Indexes

```sql
-- Automatic indexes (Primary Keys, Unique constraints)
CREATE UNIQUE INDEX users_email_idx ON users(email);
CREATE UNIQUE INDEX categories_slug_idx ON categories(slug);
CREATE UNIQUE INDEX products_slug_idx ON products(slug);
CREATE UNIQUE INDEX products_sku_idx ON products(sku);
CREATE UNIQUE INDEX product_variants_sku_idx ON product_variants(sku);

-- Custom indexes for performance
CREATE INDEX products_category_active_idx ON products(category_id, is_active);
CREATE INDEX products_price_idx ON products(price);
CREATE INDEX products_created_at_idx ON products(created_at);
CREATE INDEX products_stock_idx ON products(is_active, stock_quantity);

-- Composite indexes for complex queries
CREATE INDEX products_category_price_idx ON products(category_id, price);
CREATE INDEX products_featured_active_idx ON products(is_active, is_featured);

-- Cart and payment indexes
CREATE INDEX carts_user_status_idx ON carts(user_id, status);
CREATE INDEX cart_items_cart_product_idx ON cart_items(cart_id, product_id);
CREATE INDEX transactions_user_status_idx ON transactions(user_id, status);
CREATE INDEX transactions_provider_status_idx ON transactions(payment_provider_id, status);
```

## 📈 Performance Considerations

### Query Optimization Examples

```python
# Optimized queries using select_related and prefetch_related
from django.db import models

class ProductManager(models.Manager):
    """Custom manager for optimized queries."""
    
    def with_category(self):
        """Products with category data."""
        return self.select_related('category', 'created_by')
    
    def with_images_and_variants(self):
        """Products with images and variants."""
        return self.prefetch_related(
            'images', 
            'variants__images',
            'variants__option_values__option',
            'variants__option_values__value'
        )
    
    def active(self):
        """Active products only."""
        return self.filter(is_active=True)
    
    def in_stock(self):
        """Products in stock (including variants)."""
        return self.filter(
            models.Q(track_inventory=False) |
            models.Q(stock_quantity__gt=0) |
            models.Q(variants__stock_quantity__gt=0)
        )
    
    def with_variants_in_stock(self):
        """Products with at least one variant in stock."""
        return self.filter(
            models.Q(track_inventory=False) |
            models.Q(variants__stock_quantity__gt=0, variants__is_active=True)
        ).distinct()

# Usage in views
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Product.objects.with_category().with_images_and_variants().active()
```

### Caching Strategy

```python
# Cache frequently accessed data
from django.core.cache import cache

class CategoryManager(models.Manager):
    def get_cached_tree(self):
        """Get hierarchical categories from cache."""
        cache_key = 'category_tree'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(
                self.filter(is_active=True)
                .select_related('parent')
                .order_by('sort_order', 'name')
                .values('id', 'name', 'slug', 'parent_id')
            )
            cache.set(cache_key, categories, 3600)  # 1 hour
        
        return categories

class CartManager(models.Manager):
    def get_or_create_for_user(self, user=None, session_key=None):
        """Get or create cart for user or session."""
        if user:
            cart, created = self.get_or_create(
                user=user, 
                status=Cart.Status.ACTIVE,
                defaults={'expires_at': timezone.now() + timedelta(days=30)}
            )
        else:
            cart, created = self.get_or_create(
                session_key=session_key,
                status=Cart.Status.ACTIVE,
                defaults={'expires_at': timezone.now() + timedelta(days=7)}
            )
        return cart
```

## 🔒 Security & Constraints

### Data Integrity
- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate slugs, SKUs, and emails
- Check constraints ensure positive prices, stock quantities, and amounts
- UUID primary keys prevent ID enumeration attacks

### Access Control
- Role-based user permissions (customer, staff, admin, super_admin)
- Product creation restricted to staff/admin users
- Payment information encrypted and secured
- Cart isolation per user/session

### Audit Trail
- All tables include `created_at` and `updated_at` timestamps
- `created_by` field tracks product authorship
- User activity logging for security monitoring
- Transaction audit trail for financial compliance

## 📊 Current Implementation Status

### ✅ Implemented Models
- **Users & Authentication:** Complete with roles, verification, and security features
- **Categories:** Hierarchical system with full CRUD operations
- **Products:** Complete with variants, images, and SEO optimization
- **Product Variants:** Full variant system with options and values
- **Tags:** Product tagging system
- **Payment System:** Providers, methods, and transaction tracking
- **Shopping Cart:** Full cart and cart item functionality

### 🚧 Future Enhancements
- **Orders & Order Items:** Convert carts to orders
- **Inventory Management:** Advanced stock tracking and alerts
- **Shipping:** Shipping methods and rate calculation
- **Discounts & Coupons:** Promotional pricing system
- **Reviews & Ratings:** Product feedback system
- **Wishlist:** User product wishlists

## 📈 Data Volumes (Current)

After seeding and development usage:
- **Users:** ~10-50 (1 admin, staff users, customers)
- **Categories:** ~25-50 (hierarchical structure)
- **Tags:** ~20-30 product tags
- **Products:** ~50-100 with variants
- **Product Variants:** ~200-500 (multiple per product)
- **Product Images:** ~100-300 (multiple per product/variant)
- **Payment Providers:** ~3-5 (Chapa, Stripe, etc.)
- **Carts:** ~10-50 active carts
- **Transactions:** ~50-200 payment records

This provides a robust foundation for a modern e-commerce platform with comprehensive product management, payment processing, and user experience features.

````

### 1. User Model (Extended)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    """Extended user model with additional fields."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        help_text="User's email address (used for login)"
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text="User's phone number"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether user has verified their email"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text="User's profile picture"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
```

### 2. Category Model

```python
class Category(models.Model):
    """Product category model."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (unique)"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly category identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    image = models.ImageField(
        upload_to='categories/',
        null=True,
        blank=True,
        help_text="Category image"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Parent category for hierarchy"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether category is active"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
```

### 3. Product Model

```python
from django.core.validators import MinValueValidator
from decimal import Decimal

class Product(models.Model):
    """Product model with comprehensive fields."""
    
    name = models.CharField(
        max_length=255,
        help_text="Product name"
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly product identifier"
    )
    description = models.TextField(
        help_text="Detailed product description"
    )
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief product summary"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stock Keeping Unit"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Product price in USD"
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price (for discounts)"
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price (admin only)"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        help_text="Product category"
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        help_text="Product tags for filtering"
    )
    
    # Inventory
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Low stock warning threshold"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether product is active"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether product is featured"
    )
    is_digital = models.BooleanField(
        default=False,
        help_text="Whether product is digital"
    )
    
    # SEO
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta title"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
            # Composite indexes for filtering
            models.Index(fields=['category', 'price']),
            models.Index(fields=['is_active', 'stock_quantity']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
```

### 4. Product Images Model

```python
class ProductImage(models.Model):
    """Product image model for multiple images per product."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/',
        help_text="Product image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary image"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]
```

### 5. Tag Model

```python
class Tag(models.Model):
    """Tag model for product categorization."""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag name"
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="URL-friendly tag identifier"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Tag color (hex code)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tags'
        ordering = ['name']
```

### 6. Cart Model (Future)

```python
class Cart(models.Model):
    """Shopping cart model."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts'
    )
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Session key for anonymous users"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]

class CartItem(models.Model):
    """Cart item model."""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product']
```

### 7. Order Models (Future)

```python
class Order(models.Model):
    """Order model."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    order_number = models.CharField(
        max_length=32,
        unique=True,
        help_text="Unique order number"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Pricing
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Order subtotal"
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax amount"
    )
    shipping_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Shipping cost"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total order amount"
    )
    
    # Addresses (stored as JSON for flexibility)
    billing_address = models.JSONField(
        help_text="Billing address information"
    )
    shipping_address = models.JSONField(
        help_text="Shipping address information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['created_at']),
        ]

class OrderItem(models.Model):
    """Order item model."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    product_name = models.CharField(
        max_length=255,
        help_text="Product name at time of order"
    )
    product_sku = models.CharField(
        max_length=100,
        help_text="Product SKU at time of order"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price at time of order"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total price for this item"
    )
    
    class Meta:
        db_table = 'order_items'
```

## 🔍 Database Indexes Strategy

### Primary Indexes

```sql
-- Automatic indexes (Primary Keys, Unique constraints)
CREATE UNIQUE INDEX users_email_idx ON users(email);
CREATE UNIQUE INDEX categories_slug_idx ON categories(slug);
CREATE UNIQUE INDEX products_slug_idx ON products(slug);
CREATE UNIQUE INDEX products_sku_idx ON products(sku);

-- Custom indexes for performance
CREATE INDEX products_category_active_idx ON products(category_id, is_active);
CREATE INDEX products_price_idx ON products(price);
CREATE INDEX products_created_at_idx ON products(created_at);
CREATE INDEX products_stock_idx ON products(is_active, stock_quantity);

-- Composite indexes for complex queries
CREATE INDEX products_category_price_idx ON products(category_id, price);
CREATE INDEX products_featured_active_idx ON products(is_active, is_featured);
```

### Query Optimization Examples

```python
# Optimized queries using select_related and prefetch_related
from django.db import models

class ProductManager(models.Manager):
    """Custom manager for optimized queries."""
    
    def with_category(self):
        """Products with category data."""
        return self.select_related('category')
    
    def with_images(self):
        """Products with images."""
        return self.prefetch_related('images')
    
    def active(self):
        """Active products only."""
        return self.filter(is_active=True)
    
    def in_stock(self):
        """Products in stock."""
        return self.filter(
            models.Q(track_inventory=False) |
            models.Q(stock_quantity__gt=0)
        )
    
    def featured(self):
        """Featured products."""
        return self.filter(is_featured=True, is_active=True)
    
    def by_category(self, category_slug):
        """Products by category slug."""
        return self.filter(
            category__slug=category_slug,
            is_active=True
        ).select_related('category')

# Usage in views
class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Product.objects.with_category().with_images().active()
```

## 📈 Performance Considerations

### Database Connection Pooling

```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', 5432),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
    }
}
```

### Caching Strategy

```python
# Cache frequently accessed data
from django.core.cache import cache

class CategoryManager(models.Manager):
    def get_cached_categories(self):
        """Get categories from cache."""
        cache_key = 'active_categories'
        categories = cache.get(cache_key)
        
        if categories is None:
            categories = list(
                self.filter(is_active=True)
                .order_by('sort_order', 'name')
                .values('id', 'name', 'slug')
            )
            cache.set(cache_key, categories, 3600)  # 1 hour
        
        return categories
```

### Full-Text Search (Future)

```python
# PostgreSQL full-text search
from django.contrib.postgres.search import SearchVector, SearchRank

class ProductSearchManager(models.Manager):
    def search(self, query):
        """Full-text search on products."""
        return self.annotate(
            search=SearchVector('name', 'description', 'short_description'),
            rank=SearchRank(SearchVector('name', 'description'), query)
        ).filter(search=query).order_by('-rank')
```

## 🔄 Migration Strategy

### Initial Migration

```python
# Migration for core models
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    
    operations = [
        # Create tables with proper indexes
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",  # For similarity search
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;"
        ),
        # ... model creation operations
    ]
```

### Data Migration Example

```python
# Data migration for sample data
from django.db import migrations

def create_sample_categories(apps, schema_editor):
    """Create initial categories."""
    Category = apps.get_model('categories', 'Category')
    
    categories = [
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Clothing', 'slug': 'clothing'},
        {'name': 'Books', 'slug': 'books'},
        {'name': 'Home & Garden', 'slug': 'home-garden'},
    ]
    
    for cat_data in categories:
        Category.objects.get_or_create(**cat_data)

class Migration(migrations.Migration):
    dependencies = [
        ('categories', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            create_sample_categories,
            reverse_code=migrations.RunPython.noop
        ),
    ]
```

## 📊 Database Monitoring

### Useful SQL Queries

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

This database schema provides a solid foundation for the e-commerce platform with proper indexing, relationships, and performance considerations.
