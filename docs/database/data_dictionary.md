# 📚 Bazary Database Data Dictionary

**Last Updated:** August 2, 2025  
**Purpose:** Comprehensive field-by-field documentation of all database tables

---

## 📋 Table of Contents

1. [Users Table](#-users-table)
2. [Categories Table](#-categories-table)
3. [Products Table](#-products-table)
4. [Product Images Table](#-product-images-table)
5. [Tags Table](#-tags-table)
6. [Products-Tags Junction Table](#-products-tags-junction-table)
7. [Data Validation Rules](#-data-validation-rules)
8. [Field Naming Conventions](#-field-naming-conventions)

---

## 👥 Users Table

**Table Name:** `users`  
**Purpose:** Extended Django user model for authentication and user profiles  
**Primary Key:** `id` (UUID)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | UUID | - | ❌ | `uuid4()` | ✅ | ✅ | Primary key, unique user identifier | System generated, immutable | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `username` | VARCHAR | 150 | ❌ | - | ✅ | ✅ | Login username | Alphanumeric + underscore, 3-150 chars | `john_doe`, `admin`, `sarah123` |
| `email` | VARCHAR | 254 | ❌ | - | ✅ | ✅ | Primary email address | Valid email format, used for login | `john@example.com`, `admin@bazary.com` |
| `first_name` | VARCHAR | 150 | ✅ | `''` | ❌ | ❌ | User's first name | Optional, display purposes | `John`, `Sarah`, `Ahmed` |
| `last_name` | VARCHAR | 150 | ✅ | `''` | ❌ | ❌ | User's last name | Optional, display purposes | `Doe`, `Johnson`, `Ali` |
| `phone_number` | VARCHAR | 15 | ✅ | `NULL` | ❌ | ❌ | Contact phone number | Optional, international format preferred | `+1234567890`, `555-123-4567` |
| `is_verified` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ✅ | Email verification status | Set to true after email verification | `true`, `false` |
| `date_of_birth` | DATE | - | ✅ | `NULL` | ❌ | ❌ | User's birth date | Optional, for age-restricted products | `1990-05-15`, `1985-12-01` |
| `avatar` | VARCHAR | 100 | ✅ | `NULL` | ❌ | ❌ | Profile picture file path | Optional, relative path to media | `avatars/user123.jpg` |
| `is_active` | BOOLEAN | - | ❌ | `TRUE` | ❌ | ✅ | Account active status | Controls login ability | `true`, `false` |
| `is_staff` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ✅ | Staff access flag | Grants admin panel access | `true`, `false` |
| `is_superuser` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ✅ | Superuser access flag | Full admin permissions | `true`, `false` |
| `date_joined` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ✅ | Account creation timestamp | Auto-set on registration | `2025-01-15 10:30:00+00` |
| `last_login` | TIMESTAMP | - | ✅ | `NULL` | ❌ | ❌ | Last login timestamp | Updated on each login | `2025-08-02 14:22:15+00` |

### Users Table Business Rules

- **Registration:** Username and email must be unique across all users
- **Authentication:** Users can login with either username or email
- **Email Verification:** New users start with `is_verified=false`
- **Account Deactivation:** Setting `is_active=false` prevents login but preserves data
- **Staff Permissions:** `is_staff=true` required for product creation and admin access
- **Data Retention:** User accounts are soft-deleted (deactivated) rather than hard-deleted

---

## 🏷️ Categories Table

**Table Name:** `categories`  
**Purpose:** Hierarchical product organization system  
**Primary Key:** `id` (BIGINT)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | BIGINT | - | ❌ | `AUTO_INCREMENT` | ✅ | ✅ | Primary key, category identifier | System generated | `1`, `25`, `157` |
| `name` | VARCHAR | 100 | ❌ | - | ✅ | ✅ | Category display name | 1-100 chars, human readable | `Electronics`, `Smartphones`, `Men's Clothing` |
| `slug` | VARCHAR | 100 | ❌ | - | ✅ | ✅ | URL-friendly identifier | Lowercase, hyphens, auto-generated from name | `electronics`, `smartphones`, `mens-clothing` |
| `description` | TEXT | - | ✅ | `''` | ❌ | ❌ | Category description | Optional marketing text | `Latest electronic devices and gadgets` |
| `image` | VARCHAR | 100 | ✅ | `NULL` | ❌ | ❌ | Category image file path | Optional, relative path to media | `categories/electronics.jpg` |
| `parent_id` | BIGINT | - | ✅ | `NULL` | ❌ | ✅ | Parent category reference | NULL for root categories | `1`, `5`, `NULL` |
| `is_active` | BOOLEAN | - | ❌ | `TRUE` | ❌ | ✅ | Category active status | Controls visibility | `true`, `false` |
| `sort_order` | INTEGER | - | ❌ | `0` | ❌ | ✅ | Display sort order | Lower numbers display first | `0`, `10`, `100` |
| `created_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Creation timestamp | Auto-set on creation | `2025-01-15 10:30:00+00` |
| `updated_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Last update timestamp | Auto-updated on save | `2025-08-02 14:22:15+00` |

### Categories Table Business Rules

- **Hierarchy:** Self-referencing relationship through `parent_id`
- **Root Categories:** Have `parent_id = NULL`
- **Slug Generation:** Auto-generated from name, must be unique
- **Cascading Deletion:** Deleting parent deletes all children
- **Product Protection:** Cannot delete category with active products
- **Ordering:** Categories sorted by `sort_order` then `name`

---

## 📦 Products Table

**Table Name:** `products`  
**Purpose:** Core product catalog with comprehensive product information  
**Primary Key:** `id` (BIGINT)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | BIGINT | - | ❌ | `AUTO_INCREMENT` | ✅ | ✅ | Primary key, product identifier | System generated | `1`, `2547`, `98765` |
| `name` | VARCHAR | 255 | ❌ | - | ❌ | ✅ | Product display name | 1-255 chars, searchable | `iPhone 15 Pro`, `Samsung Galaxy S24`, `Nike Air Max` |
| `slug` | VARCHAR | 255 | ❌ | - | ✅ | ✅ | URL-friendly identifier | Auto-generated from name, unique | `iphone-15-pro`, `samsung-galaxy-s24` |
| `description` | TEXT | - | ❌ | - | ❌ | ❌ | Detailed product description | Rich text, supports markdown | `The latest iPhone with advanced camera...` |
| `short_description` | VARCHAR | 500 | ✅ | `''` | ❌ | ❌ | Brief product summary | Used in product cards | `Latest iPhone with Pro camera system` |
| `sku` | VARCHAR | 100 | ❌ | - | ✅ | ✅ | Stock keeping unit | Alphanumeric, inventory tracking | `IPH15PRO001`, `SAM-GAL-S24-BLK` |
| `price` | DECIMAL(10,2) | - | ❌ | - | ❌ | ✅ | Current selling price | Positive decimal, 2 decimal places | `999.99`, `1299.00`, `49.95` |
| `compare_price` | DECIMAL(10,2) | - | ✅ | `NULL` | ❌ | ❌ | Original/compare price | Used for showing discounts | `1199.99`, `1599.00` |
| `cost_price` | DECIMAL(10,2) | - | ✅ | `NULL` | ❌ | ❌ | Product cost price | Internal use, profit calculation | `750.00`, `980.00` |
| `category_id` | BIGINT | - | ❌ | - | ❌ | ✅ | Product category reference | Must reference active category | `1`, `15`, `43` |
| `track_inventory` | BOOLEAN | - | ❌ | `TRUE` | ❌ | ❌ | Enable inventory tracking | Controls stock management | `true`, `false` |
| `stock_quantity` | INTEGER | - | ❌ | `0` | ❌ | ✅ | Current stock level | Non-negative integer | `50`, `0`, `999` |
| `low_stock_threshold` | INTEGER | - | ❌ | `10` | ❌ | ❌ | Low stock warning level | Triggers notifications | `5`, `10`, `25` |
| `is_active` | BOOLEAN | - | ❌ | `TRUE` | ❌ | ✅ | Product active status | Controls visibility | `true`, `false` |
| `is_featured` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ✅ | Featured product flag | Used for homepage display | `true`, `false` |
| `is_digital` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ❌ | Digital product flag | No shipping required | `true`, `false` |
| `meta_title` | VARCHAR | 255 | ✅ | `''` | ❌ | ❌ | SEO meta title | Page title for search engines | `iPhone 15 Pro - Best Price Online` |
| `meta_description` | TEXT | - | ✅ | `''` | ❌ | ❌ | SEO meta description | Page description for search engines | `Buy iPhone 15 Pro with fast shipping...` |
| `created_by_id` | UUID | - | ❌ | - | ❌ | ✅ | Product creator reference | Must be staff or admin user | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `created_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ✅ | Creation timestamp | Auto-set on creation | `2025-01-15 10:30:00+00` |
| `updated_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Last update timestamp | Auto-updated on save | `2025-08-02 14:22:15+00` |

### Products Table Business Rules

- **Pricing:** All prices must be positive, compare_price typically > price
- **Inventory:** Stock quantity cannot be negative
- **SKU:** Must be unique across all products, used for inventory management
- **Categories:** Product must belong to an active category
- **Creator:** Only staff/admin users can create products
- **Slug Generation:** Auto-generated from name, must be unique
- **Digital Products:** `is_digital=true` bypasses shipping calculations

---

## 🖼️ Product Images Table

**Table Name:** `product_images`  
**Purpose:** Multiple images per product with ordering and primary designation  
**Primary Key:** `id` (BIGINT)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | BIGINT | - | ❌ | `AUTO_INCREMENT` | ✅ | ✅ | Primary key, image identifier | System generated | `1`, `2547`, `98765` |
| `product_id` | BIGINT | - | ❌ | - | ❌ | ✅ | Associated product reference | Must reference existing product | `1`, `2547`, `98765` |
| `image` | VARCHAR | 100 | ❌ | - | ❌ | ❌ | Image file path | Relative path to media directory | `products/iphone-15-pro-main.jpg` |
| `alt_text` | VARCHAR | 255 | ✅ | `''` | ❌ | ❌ | Accessibility alt text | Description for screen readers | `iPhone 15 Pro front view in Space Black` |
| `is_primary` | BOOLEAN | - | ❌ | `FALSE` | ❌ | ✅ | Primary image flag | Only one primary per product | `true`, `false` |
| `sort_order` | INTEGER | - | ❌ | `0` | ❌ | ✅ | Display order | Lower numbers display first | `0`, `1`, `2`, `10` |
| `created_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Upload timestamp | Auto-set on creation | `2025-01-15 10:30:00+00` |
| `updated_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Last update timestamp | Auto-updated on save | `2025-08-02 14:22:15+00` |

### Product Images Table Business Rules

- **Primary Image:** Only one image per product can have `is_primary=true`
- **Cascade Deletion:** Deleting product deletes all associated images
- **File Management:** Images stored in `MEDIA_ROOT/products/` directory
- **Ordering:** Images displayed in `sort_order` then `created_at` order
- **Alt Text:** Recommended for accessibility and SEO

---

## 🏷️ Tags Table

**Table Name:** `tags`  
**Purpose:** Product labeling and categorization system  
**Primary Key:** `id` (BIGINT)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | BIGINT | - | ❌ | `AUTO_INCREMENT` | ✅ | ✅ | Primary key, tag identifier | System generated | `1`, `25`, `157` |
| `name` | VARCHAR | 50 | ❌ | - | ✅ | ✅ | Tag display name | 1-50 chars, human readable | `New`, `Popular`, `Sale`, `Premium` |
| `slug` | VARCHAR | 50 | ❌ | - | ✅ | ✅ | URL-friendly identifier | Auto-generated from name | `new`, `popular`, `sale`, `premium` |
| `color` | VARCHAR | 7 | ❌ | `#007bff` | ❌ | ❌ | Display color (hex code) | Valid hex color code | `#28a745`, `#dc3545`, `#ffc107` |
| `created_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Creation timestamp | Auto-set on creation | `2025-01-15 10:30:00+00` |
| `updated_at` | TIMESTAMP | - | ❌ | `NOW()` | ❌ | ❌ | Last update timestamp | Auto-updated on save | `2025-08-02 14:22:15+00` |

### Tags Table Business Rules

- **Name:** Must be unique, case-insensitive
- **Slug:** Auto-generated from name, used in URLs
- **Color:** Hex color code for visual display (badges, labels)
- **Usage:** Tags applied to products via many-to-many relationship

---

## 🔗 Products-Tags Junction Table

**Table Name:** `products_tags`  
**Purpose:** Many-to-many relationship between products and tags  
**Primary Key:** `id` (BIGINT)

| Field Name | Data Type | Max Length | Null | Default | Unique | Index | Description | Business Rules | Example Values |
|------------|-----------|------------|------|---------|--------|-------|-------------|----------------|----------------|
| `id` | BIGINT | - | ❌ | `AUTO_INCREMENT` | ✅ | ✅ | Primary key, junction record ID | System generated | `1`, `2547`, `98765` |
| `product_id` | BIGINT | - | ❌ | - | ❌ | ✅ | Product reference | Must reference existing product | `1`, `2547`, `98765` |
| `tag_id` | BIGINT | - | ❌ | - | ❌ | ✅ | Tag reference | Must reference existing tag | `1`, `5`, `12` |

### Junction Table Business Rules

- **Unique Constraint:** `(product_id, tag_id)` combination must be unique
- **Cascade Deletion:** Deleting product or tag removes associations
- **No Direct Management:** Managed through Product.tags relationship

---

## ✅ Data Validation Rules

### Field Length Constraints

| Data Type | Max Length | Validation Rule | Example |
|-----------|------------|-----------------|---------|
| VARCHAR(50) | 50 chars | Length validation in forms | Tag names, short identifiers |
| VARCHAR(100) | 100 chars | Medium text fields | Category names, file paths |
| VARCHAR(150) | 150 chars | User names, longer identifiers | First name, last name, username |
| VARCHAR(255) | 255 chars | Long text fields | Product names, meta titles |
| VARCHAR(500) | 500 chars | Short descriptions | Product short descriptions |
| TEXT | Unlimited | Long content | Product descriptions, meta descriptions |

### Numeric Constraints

| Field Type | Constraint | Validation | Example |
|------------|------------|------------|---------|
| DECIMAL(10,2) | 10 digits, 2 decimal | Price validation | `9999999.99` max |
| INTEGER | 32-bit signed | Range validation | `-2,147,483,648` to `2,147,483,647` |
| BIGINT | 64-bit signed | Large numbers | Product/category IDs |

### Format Validation

| Field | Format Rule | Regex/Validation | Example |
|-------|-------------|------------------|---------|
| Email | RFC 5322 | Django EmailValidator | `user@example.com` |
| Phone | International | Optional `+` prefix | `+1234567890` |
| Slug | URL-safe | `^[-a-zA-Z0-9_]+$` | `product-name-123` |
| Hex Color | Hex format | `^#[0-9A-Fa-f]{6}$` | `#FF5733` |
| UUID | UUID4 format | Standard UUID validation | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |

---

## 📝 Field Naming Conventions

### General Rules

1. **Snake Case:** All field names use `snake_case` convention
2. **Descriptive Names:** Fields should be self-documenting
3. **Consistent Suffixes:**
   - `_id` for foreign key fields
   - `_at` for timestamp fields
   - `is_` prefix for boolean fields
   - `_url` for URL fields
   - `_path` for file path fields

### Standard Field Patterns

| Pattern | Purpose | Examples |
|---------|---------|----------|
| `created_at` | Creation timestamp | `created_at`, `uploaded_at` |
| `updated_at` | Modification timestamp | `updated_at`, `modified_at` |
| `is_active` | Boolean status flags | `is_active`, `is_featured`, `is_verified` |
| `*_id` | Foreign key references | `category_id`, `created_by_id`, `parent_id` |
| `*_count` | Numeric counters | `stock_quantity`, `sort_order`, `view_count` |
| `meta_*` | SEO-related fields | `meta_title`, `meta_description` |

### Boolean Field Naming

| Field | Purpose | True Meaning | False Meaning |
|-------|---------|--------------|---------------|
| `is_active` | Status control | Visible/available | Hidden/disabled |
| `is_featured` | Promotion flag | Featured/highlighted | Normal display |
| `is_verified` | Verification status | Verified/confirmed | Unverified/pending |
| `is_digital` | Product type | Digital/downloadable | Physical/shippable |
| `is_primary` | Selection flag | Primary/main | Secondary/additional |
| `track_inventory` | Feature toggle | Tracking enabled | Tracking disabled |

This data dictionary provides comprehensive documentation for all database fields, ensuring consistent development and maintenance of the Bazary e-commerce platform.
