# 🗄️ Bazary Database Schema Documentation

**Last Updated:** August 10, 2025  
**Database:** PostgreSQL (Development: SQLite)  
**Django Version:** 5.0.14  

---

## 📊 Schema Overview

Bazary uses a PostgreSQL database with Django ORM, designed for scalability and performance optimization. The schema supports a comprehensive e-commerce platform with user management, product catalog with variants, categories, shopping cart, and payment processing.

### 🔗 Core Relationships

```
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

## 📋 Database Tables

| Table Name | Records | Purpose | Key Relationships |
|------------|---------|---------|-------------------|
| `users` | ~10-100K | User authentication & profiles | Primary auth table |
| `user_profiles` | ~10-100K | Extended user information | One-to-one with users |
| `user_addresses` | ~50-500K | User shipping/billing addresses | Many-to-one with users |
| `categories` | ~50-200 | Product organization | Self-referencing hierarchy |
| `products` | ~1K-100K | Product catalog | References categories, users |
| `product_variants` | ~5K-500K | Product variations (size, color) | References products |
| `product_images` | ~5K-500K | Product media | References products |
| `product_variant_images` | ~10K-1M | Variant-specific images | References variants |
| `variant_options` | ~20-100 | Option types (Color, Size) | Referenced by variants |
| `variant_option_values` | ~200-1K | Option values (Red, Large) | References options |
| `tags` | ~50-500 | Product labeling | Many-to-many with products |
| `carts` | ~1K-50K | Shopping carts | References users, sessions |
| `cart_items` | ~5K-200K | Cart contents | References carts, products |
| `payment_providers` | ~5-20 | Payment gateway configs | Referenced by methods |
| `payment_methods` | ~100-10K | User payment methods | References users, providers |
| `transactions` | ~1K-1M | Payment records | References users, providers |

---

## 🏗️ Core Table Structure

### 1. Users Table (`users`)

**Purpose:** Extended Django user model with e-commerce and security features

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `username` | VARCHAR(150) | UNIQUE, NOT NULL | Login username |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Primary email (login) |
| `first_name` | VARCHAR(150) | | User's first name |
| `last_name` | VARCHAR(150) | | User's last name |
| `phone_number` | VARCHAR(15) | | Contact phone number |
| `is_verified` | BOOLEAN | DEFAULT FALSE | Email verification status |
| `role` | VARCHAR(20) | DEFAULT 'customer' | User role (customer/staff/admin) |
| `is_email_verified` | BOOLEAN | DEFAULT FALSE | Email verification flag |
| `failed_login_attempts` | INTEGER | DEFAULT 0 | Failed login count |
| `account_locked_until` | TIMESTAMP | NULL | Account lock expiration |
| `date_of_birth` | DATE | NULL | User's birth date |
| `avatar` | VARCHAR(100) | NULL | Profile picture path |

**Related Tables:**
- `user_profiles` (1:1) - Extended profile information
- `user_addresses` (1:N) - Shipping/billing addresses
- `email_verification_tokens` (1:N) - Email verification
- `password_reset_tokens` (1:N) - Password reset

### 2. Products Table (`products`)

**Purpose:** Core product catalog with comprehensive product information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Product identifier |
| `name` | VARCHAR(255) | NOT NULL | Product name |
| `slug` | VARCHAR(255) | UNIQUE, NOT NULL | URL-friendly identifier |
| `sku` | VARCHAR(100) | UNIQUE, NOT NULL | Stock keeping unit |
| `price` | DECIMAL(10,2) | NOT NULL | Base price |
| `compare_price` | DECIMAL(10,2) | NULL | Original/compare price |
| `category_id` | BIGINT | FOREIGN KEY, NOT NULL | Product category |
| `stock_quantity` | INTEGER | DEFAULT 0 | Current stock level |
| `is_active` | BOOLEAN | DEFAULT TRUE | Product visibility |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Featured flag |
| `is_digital` | BOOLEAN | DEFAULT FALSE | Digital product flag |
| `track_inventory` | BOOLEAN | DEFAULT TRUE | Inventory tracking |

**Performance Indexes:**
- `products_slug_idx` - Fast slug lookups
- `products_sku_idx` - SKU searches  
- `products_category_active_idx` - Category filtering
- `products_price_idx` - Price sorting
- `products_featured_active_idx` - Featured products

### 3. Product Variants Table (`product_variants`)

**Purpose:** Product variations with individual pricing and inventory

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Variant identifier |
| `product_id` | BIGINT | FOREIGN KEY, NOT NULL | Base product |
| `sku` | VARCHAR(100) | UNIQUE, NOT NULL | Unique variant SKU |
| `price` | DECIMAL(10,2) | NULL | Variant price override |
| `stock_quantity` | INTEGER | DEFAULT 0 | Variant stock level |
| `is_active` | BOOLEAN | DEFAULT TRUE | Variant availability |
| `weight` | DECIMAL(8,2) | NULL | Weight in grams |
| `dimensions_length` | DECIMAL(8,2) | NULL | Length in cm |
| `dimensions_width` | DECIMAL(8,2) | NULL | Width in cm |
| `dimensions_height` | DECIMAL(8,2) | NULL | Height in cm |

**Variant Options System:**
- `variant_options` - Option types (Color, Size, Material)
- `variant_option_values` - Specific values (Red, Large, Cotton)
- `product_variant_options` - Links variants to option combinations

### 4. Shopping Cart Tables

#### Carts Table (`carts`)
**Purpose:** Shopping cart supporting users and guest sessions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Cart identifier |
| `user_id` | UUID | FOREIGN KEY, NULL | User (null for guests) |
| `session_key` | VARCHAR(40) | | Guest session key |
| `status` | VARCHAR(20) | DEFAULT 'active' | Cart status |
| `subtotal` | DECIMAL(10,2) | DEFAULT 0.00 | Calculated subtotal |
| `tax_amount` | DECIMAL(10,2) | DEFAULT 0.00 | Tax amount |
| `shipping_amount` | DECIMAL(10,2) | DEFAULT 0.00 | Shipping cost |
| `total` | DECIMAL(10,2) | DEFAULT 0.00 | Total amount |
| `expires_at` | TIMESTAMP | NULL | Cart expiration |

#### Cart Items Table (`cart_items`)
**Purpose:** Individual items in shopping carts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `cart_id` | UUID | FOREIGN KEY, NOT NULL | Cart reference |
| `product_id` | BIGINT | FOREIGN KEY, NOT NULL | Product reference |
| `variant_id` | BIGINT | FOREIGN KEY, NULL | Variant reference |
| `quantity` | INTEGER | NOT NULL | Item quantity |
| `unit_price` | DECIMAL(10,2) | NOT NULL | Price snapshot |
| `total_price` | DECIMAL(10,2) | NOT NULL | Calculated total |

### 5. Payment System Tables

#### Payment Providers Table (`payment_providers`)
**Purpose:** Payment gateway configurations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Provider name |
| `provider_type` | VARCHAR(20) | NOT NULL | Type (chapa/stripe/paypal) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Provider status |
| `api_key` | VARCHAR(200) | NOT NULL | API key |
| `secret_key` | VARCHAR(200) | NOT NULL | Secret key |
| `test_mode` | BOOLEAN | DEFAULT TRUE | Test/live mode |
| `supported_currencies` | JSON | | Currency list |

#### Transactions Table (`transactions`)
**Purpose:** Payment transaction records with audit trail

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Transaction ID |
| `user_id` | UUID | FOREIGN KEY, NOT NULL | User reference |
| `amount` | DECIMAL(10,2) | NOT NULL | Transaction amount |
| `currency` | VARCHAR(3) | DEFAULT 'USD' | Currency code |
| `status` | VARCHAR(20) | DEFAULT 'pending' | Transaction status |
| `external_transaction_id` | VARCHAR(200) | | Provider transaction ID |
| `processed_at` | TIMESTAMP | NULL | Processing timestamp |

---

## 🔍 Query Patterns

### Common Queries

**1. Get products with variants and images:**
```sql
SELECT p.*, pv.*, pi.image as primary_image
FROM products p
LEFT JOIN product_variants pv ON p.id = pv.product_id AND pv.is_active = true
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = true
WHERE p.category_id = ? AND p.is_active = true
ORDER BY p.created_at DESC;
```

**2. Get variant options for a product:**
```sql
SELECT vo.name as option_name, vov.value, vov.display_name, vov.color_code
FROM product_variants pv
JOIN product_variant_options pvo ON pv.id = pvo.variant_id
JOIN variant_options vo ON pvo.option_id = vo.id
JOIN variant_option_values vov ON pvo.value_id = vov.id
WHERE pv.product_id = ? AND pv.is_active = true
ORDER BY vo.sort_order, vov.sort_order;
```

**3. Get user cart with items:**
```sql
SELECT c.*, ci.quantity, ci.unit_price, p.name as product_name, 
       pv.sku as variant_sku
FROM carts c
LEFT JOIN cart_items ci ON c.id = ci.cart_id
LEFT JOIN products p ON ci.product_id = p.id
LEFT JOIN product_variants pv ON ci.variant_id = pv.id
WHERE c.user_id = ? AND c.status = 'active';
```

### Performance Optimizations

**1. Category hierarchy with CTE:**
```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 as level, ARRAY[id] as path
    FROM categories 
    WHERE parent_id IS NULL AND is_active = true
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.level + 1, ct.path || c.id
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
    WHERE c.is_active = true AND NOT c.id = ANY(ct.path)
)
SELECT * FROM category_tree ORDER BY level, name;
```

**2. Product search with variants:**
```sql
SELECT DISTINCT p.*, pi.image, 
       MIN(COALESCE(pv.price, p.price)) as min_price,
       MAX(COALESCE(pv.price, p.price)) as max_price
FROM products p
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = true
LEFT JOIN product_variants pv ON p.id = pv.product_id AND pv.is_active = true
WHERE p.name ILIKE '%search%' AND p.is_active = true
GROUP BY p.id, pi.image
ORDER BY p.created_at DESC;
```

**3. Cart totals calculation:**
```sql
UPDATE carts SET 
    subtotal = (
        SELECT COALESCE(SUM(ci.total_price), 0)
        FROM cart_items ci 
        WHERE ci.cart_id = carts.id
    ),
    total = subtotal + tax_amount + shipping_amount - discount_amount
WHERE id = ?;
```

---

## 🔒 Security & Constraints

### Data Integrity Constraints

**1. Unique Constraints:**
- Product SKUs must be unique across all products and variants
- User emails must be unique
- Category and tag slugs must be unique

**2. Foreign Key Constraints:**
- Products cannot be deleted if they have variants
- Users cannot be deleted if they have orders/transactions
- Categories cannot be deleted if they have products

**3. Check Constraints:**
```sql
-- Positive prices and quantities
ALTER TABLE products ADD CONSTRAINT positive_price CHECK (price > 0);
ALTER TABLE product_variants ADD CONSTRAINT positive_stock CHECK (stock_quantity >= 0);
ALTER TABLE cart_items ADD CONSTRAINT positive_quantity CHECK (quantity > 0);

-- Valid status values
ALTER TABLE carts ADD CONSTRAINT valid_cart_status 
CHECK (status IN ('active', 'abandoned', 'converted', 'expired'));

-- Price consistency
ALTER TABLE products ADD CONSTRAINT compare_price_higher 
CHECK (compare_price IS NULL OR compare_price >= price);
```

### Security Measures

**1. UUID Primary Keys:**
- Users table uses UUID to prevent ID enumeration
- Carts and transactions use UUID for security

**2. Role-Based Access:**
```python
# Django model permissions
class ProductPermissions:
    def has_add_permission(self, user):
        return user.has_role('staff')
    
    def has_change_permission(self, user, obj=None):
        return user.has_role('staff') or (obj and obj.created_by == user)
```

**3. Data Encryption:**
- Payment provider keys encrypted at rest
- Sensitive user data encrypted in database
- HTTPS required for all payment operations

---

## 📈 Scaling Considerations

### Current Capacity
- **Users:** Supports up to 100K users efficiently with proper indexing
- **Products:** Optimized for up to 100K products with variants
- **Transactions:** Handles millions of payment records with partitioning
- **Cart Items:** Supports high-frequency cart operations

### Performance Optimizations

**1. Database Indexes:**
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_products_category_price_active ON products(category_id, price, is_active);
CREATE INDEX idx_variants_product_stock ON product_variants(product_id, stock_quantity, is_active);
CREATE INDEX idx_cart_items_cart_product ON cart_items(cart_id, product_id, variant_id);
CREATE INDEX idx_transactions_user_status_date ON transactions(user_id, status, created_at);
```

**2. Query Optimization:**
```python
# Django ORM optimizations
class ProductQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related('category', 'created_by').prefetch_related(
            'variants__images',
            'variants__option_values__option',
            'variants__option_values__value',
            'images',
            'tags'
        )
    
    def available(self):
        return self.filter(
            is_active=True
        ).filter(
            Q(track_inventory=False) |
            Q(stock_quantity__gt=0) |
            Q(variants__stock_quantity__gt=0, variants__is_active=True)
        ).distinct()
```

**3. Caching Strategy:**
```python
# Redis caching for frequently accessed data
CACHE_KEYS = {
    'categories': 'categories:tree:v1',
    'featured_products': 'products:featured:v1',
    'cart_count': 'cart:count:{user_id}',
}

# Cache invalidation on model changes
@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    cache.delete_many([
        CACHE_KEYS['featured_products'],
        f'product:detail:{instance.slug}',
        f'category:products:{instance.category.slug}'
    ])
```

### Future Enhancements

**1. Database Partitioning:**
- Partition transactions table by date
- Partition user activity logs by month
- Consider sharding for very large deployments

**2. Read Replicas:**
- Separate read/write database connections
- Route read queries to replica databases
- Cache frequently accessed reference data

**3. Search Integration:**
- Elasticsearch for advanced product search
- Full-text search with relevance scoring
- Faceted search with filters and aggregations

---

## 🔄 Migration Strategy

### Current Migrations Status
- ✅ **Initial Setup:** User authentication and core models
- ✅ **Product Catalog:** Products, categories, tags, images
- ✅ **Product Variants:** Comprehensive variant system
- ✅ **Payment System:** Providers, methods, transactions
- ✅ **Shopping Cart:** Cart and cart items
- 🚧 **Orders System:** Future enhancement
- 🚧 **Inventory Management:** Advanced stock tracking
- 🚧 **Shipping:** Shipping methods and calculations

### Data Seeding
```python
# Management command for development data
python manage.py seed_development_data --users=20 --products=100 --variants=300
```

---

## 📊 Data Volumes (Current)

After comprehensive development and testing:
- **Users:** ~50 (varied roles and verification states)
- **Categories:** ~30 (hierarchical structure with 2-3 levels)
- **Products:** ~100 (with realistic variety)
- **Product Variants:** ~300 (size/color combinations)
- **Product Images:** ~200 (multiple per product)
- **Tags:** ~25 (promotional and descriptive tags)
- **Payment Providers:** ~3 (Chapa, Stripe test configs)
- **Carts:** ~20 (active user carts)
- **Cart Items:** ~50 (various products and quantities)
- **Transactions:** ~100 (test payment records)

This provides a comprehensive testing environment with realistic data relationships and sufficient complexity for development and API testing.

---

## 📋 Database Tables

| Table Name | Records | Purpose | Key Relationships |
|------------|---------|---------|-------------------|
| `users` | ~10-100K | User authentication & profiles | Primary auth table |
| `categories` | ~50-200 | Product organization | Self-referencing hierarchy |
| `products` | ~1K-100K | Product catalog | References categories, users |
| `product_images` | ~5K-500K | Product media | References products |
| `tags` | ~50-500 | Product labeling | Many-to-many with products |

---

## 🏗️ Table Structure

### 1. Users Table (`users`)

**Purpose:** Extended Django user model with e-commerce specific fields

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `username` | VARCHAR(150) | UNIQUE, NOT NULL | Login username |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Primary email (login) |
| `first_name` | VARCHAR(150) | | User's first name |
| `last_name` | VARCHAR(150) | | User's last name |
| `phone_number` | VARCHAR(15) | | Contact phone number |
| `is_verified` | BOOLEAN | DEFAULT FALSE | Email verification status |
| `date_of_birth` | DATE | NULL | User's birth date |
| `avatar` | VARCHAR(100) | NULL | Profile picture path |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active status |
| `is_staff` | BOOLEAN | DEFAULT FALSE | Staff access flag |
| `is_superuser` | BOOLEAN | DEFAULT FALSE | Admin access flag |
| `date_joined` | TIMESTAMP | NOT NULL | Account creation date |
| `last_login` | TIMESTAMP | NULL | Last login timestamp |

**Indexes:**
- `users_email_idx` - Fast email lookups for authentication
- `users_username_idx` - Username searches
- `users_date_joined_idx` - User registration analytics

**Sample Data:**
```sql
-- Admin user
INSERT INTO users (id, username, email, first_name, last_name, is_superuser, is_staff)
VALUES ('admin-uuid', 'admin', 'admin@bazary.com', 'Admin', 'User', true, true);

-- Regular customer
INSERT INTO users (id, username, email, first_name, last_name, is_verified)
VALUES ('customer-uuid', 'john_doe', 'john@example.com', 'John', 'Doe', true);
```

---

### 2. Categories Table (`categories`)

**Purpose:** Hierarchical product organization system

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Category identifier |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Category name |
| `slug` | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly identifier |
| `description` | TEXT | | Category description |
| `image` | VARCHAR(100) | NULL | Category image path |
| `parent_id` | BIGINT | FOREIGN KEY | Parent category (self-ref) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Category active status |
| `sort_order` | INTEGER | DEFAULT 0 | Display order |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Relationships:**
- `parent_id` → `categories.id` (Self-referencing for hierarchy)

**Indexes:**
- `categories_slug_idx` - Fast slug lookups for URLs
- `categories_parent_idx` - Hierarchy queries
- `categories_is_active_idx` - Active category filtering
- `categories_sort_order_idx` - Ordered display

**Sample Data:**
```sql
-- Parent category
INSERT INTO categories (name, slug, description, is_active, sort_order)
VALUES ('Electronics', 'electronics', 'Electronic devices and gadgets', true, 10);

-- Child category
INSERT INTO categories (name, slug, description, parent_id, is_active, sort_order)
VALUES ('Smartphones', 'smartphones', 'Mobile phones and accessories', 1, true, 10);
```

---

### 3. Products Table (`products`)

**Purpose:** Core product catalog with comprehensive product information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Product identifier |
| `name` | VARCHAR(255) | NOT NULL | Product name |
| `slug` | VARCHAR(255) | UNIQUE, NOT NULL | URL-friendly identifier |
| `description` | TEXT | NOT NULL | Detailed description |
| `short_description` | VARCHAR(500) | | Brief product summary |
| `sku` | VARCHAR(100) | UNIQUE, NOT NULL | Stock keeping unit |
| `price` | DECIMAL(10,2) | NOT NULL | Current price |
| `compare_price` | DECIMAL(10,2) | NULL | Original/compare price |
| `cost_price` | DECIMAL(10,2) | NULL | Cost price (admin only) |
| `category_id` | BIGINT | FOREIGN KEY, NOT NULL | Product category |
| `track_inventory` | BOOLEAN | DEFAULT TRUE | Inventory tracking flag |
| `stock_quantity` | INTEGER | DEFAULT 0 | Current stock level |
| `low_stock_threshold` | INTEGER | DEFAULT 10 | Low stock warning level |
| `is_active` | BOOLEAN | DEFAULT TRUE | Product active status |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Featured product flag |
| `is_digital` | BOOLEAN | DEFAULT FALSE | Digital product flag |
| `meta_title` | VARCHAR(255) | | SEO meta title |
| `meta_description` | TEXT | | SEO meta description |
| `created_by_id` | UUID | FOREIGN KEY | Product creator |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Relationships:**
- `category_id` → `categories.id`
- `created_by_id` → `users.id`
- Many-to-many with `tags` via junction table

**Indexes:**
- `products_slug_idx` - Fast slug lookups for URLs
- `products_sku_idx` - SKU lookups for inventory
- `products_category_is_active_idx` - Category filtering
- `products_is_active_is_featured_idx` - Featured products
- `products_price_idx` - Price-based sorting/filtering
- `products_created_at_idx` - Chronological ordering
- `products_category_price_idx` - Combined category/price filtering
- `products_is_active_stock_idx` - Stock availability queries

**Sample Data:**
```sql
INSERT INTO products (name, slug, description, sku, price, category_id, stock_quantity, is_active, created_by_id)
VALUES ('iPhone 15 Pro', 'iphone-15-pro', 'Latest iPhone with advanced features', 'IPH15PRO001', 999.99, 2, 50, true, 'admin-uuid');
```

---

### 4. Product Images Table (`product_images`)

**Purpose:** Multiple images per product with ordering and primary image designation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Image identifier |
| `product_id` | BIGINT | FOREIGN KEY, NOT NULL | Associated product |
| `image` | VARCHAR(100) | NOT NULL | Image file path |
| `alt_text` | VARCHAR(255) | | Accessibility alt text |
| `is_primary` | BOOLEAN | DEFAULT FALSE | Primary image flag |
| `sort_order` | INTEGER | DEFAULT 0 | Display order |
| `created_at` | TIMESTAMP | NOT NULL | Upload timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Relationships:**
- `product_id` → `products.id` (CASCADE DELETE)

**Indexes:**
- `product_images_product_is_primary_idx` - Primary image queries

**Sample Data:**
```sql
INSERT INTO product_images (product_id, image, alt_text, is_primary, sort_order)
VALUES (1, 'products/iphone-15-pro-main.jpg', 'iPhone 15 Pro front view', true, 0);
```

---

### 5. Tags Table (`tags`)

**Purpose:** Product labeling and categorization system

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Tag identifier |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Tag name |
| `slug` | VARCHAR(50) | UNIQUE, NOT NULL | URL-friendly identifier |
| `color` | VARCHAR(7) | DEFAULT '#007bff' | Display color (hex) |
| `created_at` | TIMESTAMP | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |

**Sample Data:**
```sql
INSERT INTO tags (name, slug, color)
VALUES ('New', 'new', '#28a745'),
       ('Popular', 'popular', '#007bff'),
       ('Sale', 'sale', '#dc3545');
```

---

### 6. Product-Tags Junction Table (`products_tags`)

**Purpose:** Many-to-many relationship between products and tags

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | BIGINT | PRIMARY KEY | Junction record ID |
| `product_id` | BIGINT | FOREIGN KEY, NOT NULL | Product reference |
| `tag_id` | BIGINT | FOREIGN KEY, NOT NULL | Tag reference |

**Relationships:**
- `product_id` → `products.id` (CASCADE DELETE)
- `tag_id` → `tags.id` (CASCADE DELETE)

**Constraints:**
- `UNIQUE(product_id, tag_id)` - Prevent duplicate associations

---

## 🔍 Query Patterns

### Common Queries

**1. Get products by category with images:**
```sql
SELECT p.*, pi.image as primary_image
FROM products p
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = true
WHERE p.category_id = ? AND p.is_active = true
ORDER BY p.created_at DESC;
```

**2. Get category hierarchy:**
```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 as level
    FROM categories 
    WHERE parent_id IS NULL AND is_active = true
    
    UNION ALL
    
    SELECT c.id, c.name, c.parent_id, ct.level + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
    WHERE c.is_active = true
)
SELECT * FROM category_tree ORDER BY level, name;
```

**3. Search products with tags:**
```sql
SELECT DISTINCT p.*
FROM products p
LEFT JOIN products_tags pt ON p.id = pt.product_id
LEFT JOIN tags t ON pt.tag_id = t.id
WHERE (p.name ILIKE '%search%' 
       OR p.description ILIKE '%search%'
       OR t.name ILIKE '%search%')
AND p.is_active = true;
```

### Performance Considerations

**1. Use indexes for common filter combinations:**
- Category + Active status
- Price range queries
- Stock availability checks

**2. Optimize N+1 queries with select_related/prefetch_related:**
```python
# Good: Optimized query
products = Product.objects.select_related('category', 'created_by').prefetch_related('tags', 'images')

# Bad: N+1 query problem
for product in Product.objects.all():
    print(product.category.name)  # Triggers additional query
```

**3. Use database-level constraints:**
- Unique constraints on slugs and SKUs
- Foreign key constraints for data integrity
- Check constraints for positive prices

---

## 📈 Scaling Considerations

### Current Capacity
- **Users:** Supports up to 100K users efficiently
- **Products:** Optimized for up to 100K products
- **Categories:** Hierarchical structure supports deep nesting
- **Images:** Multiple images per product with CDN-ready structure

### Future Optimizations
1. **Partitioning:** Consider table partitioning for large product datasets
2. **Caching:** Redis caching for frequently accessed categories and featured products
3. **Search:** Elasticsearch integration for advanced product search
4. **CDN:** Image optimization and CDN delivery for product images

---

## 🔒 Security & Constraints

### Data Integrity
- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate slugs and SKUs
- Check constraints ensure positive prices and stock quantities

### Access Control
- User roles managed through Django's built-in permissions
- Product creation restricted to staff/admin users
- Soft delete patterns for important business data

### Audit Trail
- All tables include `created_at` and `updated_at` timestamps
- `created_by` field tracks product authorship
- Django admin logs all administrative changes

---

## 📊 Data Volumes (Development)

After seeding:
- **Users:** ~10 (1 admin, 1 staff, 8 customers)
- **Categories:** ~25 (5 parent, 20 child categories)
- **Tags:** ~10 product tags
- **Products:** ~25 sample products with realistic data
- **Product Images:** ~0 (structure ready for image uploads)

This provides a realistic testing environment with sufficient data variety for development and API testing.
