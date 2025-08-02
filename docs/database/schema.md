# 🗄️ Bazary Database Schema Documentation

**Last Updated:** August 2, 2025  
**Database:** PostgreSQL (Development: SQLite)  
**Django Version:** 5.0.14  

---

## 📊 Schema Overview

Bazary uses a PostgreSQL database with Django ORM, designed for scalability and performance optimization. The schema supports a full e-commerce platform with user management, product catalog, categories, and future shopping cart/order functionality.

### 🔗 Core Relationships

```
User (1) ────────> (*) Product (created_by)
Category (1) ────> (*) Product  
Category (1) ────> (*) Category (parent/child)
Product (*) ─────> (*) Tag (many-to-many)
Product (1) ─────> (*) ProductImage
```

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
