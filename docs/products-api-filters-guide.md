# Products API - Complete Filter & Query Parameters Guide

## 📍 Endpoint
```
GET /api/v1/products/products/
```

---

## 🔍 **Available Query Parameters**

### **1. Text Search**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search across name, description, short_description, SKU, and tags | `?search=wireless` |
| `q` | string | Alternative search parameter (same as search) | `?q=headphones` |
| `name` | string | Search by product name (partial match) | `?name__icontains=laptop` |
| `sku` | string | Search by SKU (partial match) | `?sku__icontains=ELEC` |

**Examples:**
```bash
# Basic search
GET /api/v1/products/products/?search=wireless

# Search by name
GET /api/v1/products/products/?name__icontains=laptop

# Search by SKU
GET /api/v1/products/products/?sku__icontains=ELEC-001
```

---

### **2. Category Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `category` | integer | Filter by category ID | `?category=1` |
| `category_slug` | string | Filter by category slug (lowercase, hyphenated) | `?category_slug=electronics` |

**Examples:**
```bash
# By category ID (get ID from /api/v1/categories/categories/)
GET /api/v1/products/products/?category=1

# By category slug (lowercase, use hyphens for spaces)
GET /api/v1/products/products/?category_slug=electronics

# Subcategory example
GET /api/v1/products/products/?category_slug=audio

# For multi-word categories, use hyphens
GET /api/v1/products/products/?category_slug=home-garden
```

**⚠️ Important Notes:**
- **Category slugs are lowercase** (e.g., `electronics` not `Electronics`)
- **Hierarchical filtering**: When you filter by a parent category (e.g., `electronics`), it **automatically includes products from all subcategories** (Smartphones, Laptops, Audio, Gaming)
- **Categories are NOT the same as tags**
- Use `category` or `category_slug` for categories
- Use `tag_names` for tags (see section 6)
- To see all available categories: `GET /api/v1/categories/categories/`

**💡 Hierarchical Category Example:**
```bash
# This will return products from Electronics AND all its subcategories
# (Smartphones, Laptops, Audio, Gaming)
GET /api/v1/products/products/?category_slug=electronics

# This will return only products in the specific subcategory
GET /api/v1/products/products/?category_slug=smartphones
```

---

### **3. Price Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `price_min` | decimal | Minimum price (greater than or equal) | `?price_min=50` |
| `price_max` | decimal | Maximum price (less than or equal) | `?price_max=500` |
| `price` | decimal | Exact price match | `?price=99.99` |
| `price__gte` | decimal | Price greater than or equal | `?price__gte=100` |
| `price__lte` | decimal | Price less than or equal | `?price__lte=200` |

**Examples:**
```bash
# Price range
GET /api/v1/products/products/?price_min=50&price_max=200

# Minimum price only
GET /api/v1/products/products/?price_min=100

# Maximum price only
GET /api/v1/products/products/?price_max=500

# Exact price
GET /api/v1/products/products/?price=99.99
```

---

### **4. Stock Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `in_stock` | boolean | Filter products in stock | `?in_stock=true` |
| `low_stock` | boolean | Filter products with low stock | `?low_stock=true` |
| `stock_quantity` | integer | Exact stock quantity | `?stock_quantity=10` |
| `stock_quantity__gte` | integer | Stock >= value | `?stock_quantity__gte=5` |
| `stock_quantity__lte` | integer | Stock <= value | `?stock_quantity__lte=20` |

**Examples:**
```bash
# Only in-stock products
GET /api/v1/products/products/?in_stock=true

# Out of stock products
GET /api/v1/products/products/?in_stock=false

# Low stock products
GET /api/v1/products/products/?low_stock=true

# Minimum stock quantity
GET /api/v1/products/products/?stock_quantity__gte=10
```

---

### **5. Status Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `is_featured` | boolean | Filter featured products | `?is_featured=true` |
| `is_active` | boolean | Filter active products | `?is_active=true` |
| `is_digital` | boolean | Filter digital products | `?is_digital=true` |

**Examples:**
```bash
# Featured products only
GET /api/v1/products/products/?is_featured=true

# Active products
GET /api/v1/products/products/?is_active=true

# Digital products
GET /api/v1/products/products/?is_digital=true

# Physical products (non-digital)
GET /api/v1/products/products/?is_digital=false
```

---

### **6. Tag Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `tags` | integer(s) | Filter by tag ID(s) | `?tags=1,2,3` |
| `tag_names` | string | Filter by tag names (comma-separated, case-insensitive) | `?tag_names=wireless,bluetooth` |

**Examples:**
```bash
# Single tag by ID
GET /api/v1/products/products/?tags=1

# Multiple tags by ID (OR operation - matches ANY tag)
GET /api/v1/products/products/?tags=1,2,3

# By tag names (case-insensitive)
GET /api/v1/products/products/?tag_names=wireless,bluetooth

# Single tag by name
GET /api/v1/products/products/?tag_names=audio
```

**⚠️ Important Notes:**
- **Tags are product attributes, NOT categories**
- Tags use case-insensitive matching
- Multiple tags use OR logic (matches products with ANY of the tags)
- To see all available tags: `GET /api/v1/products/tags/`
- **Don't confuse with categories** - use `category_slug` for categories!

---

### **7. Date Filters**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_after` | datetime | Products created after date | `?created_after=2025-01-01` |
| `created_before` | datetime | Products created before date | `?created_before=2025-12-31` |

**Examples:**
```bash
# Products created after Jan 1, 2025
GET /api/v1/products/products/?created_after=2025-01-01

# Products created before Dec 31, 2025
GET /api/v1/products/products/?created_before=2025-12-31

# Date range
GET /api/v1/products/products/?created_after=2025-01-01&created_before=2025-12-31

# With time
GET /api/v1/products/products/?created_after=2025-01-01T00:00:00Z
```

---

### **8. Sorting (Ordering)**

| Parameter | Values | Description | Example |
|-----------|--------|-------------|---------|
| `ordering` | Field name | Sort by field (prefix with `-` for descending) | `?ordering=price` |

**Available Sorting Fields:**
- `name` - Product name (alphabetical)
- `price` - Product price
- `created_at` - Creation date
- `stock_quantity` - Stock quantity

**Examples:**
```bash
# Sort by price (ascending)
GET /api/v1/products/products/?ordering=price

# Sort by price (descending)
GET /api/v1/products/products/?ordering=-price

# Sort by newest first
GET /api/v1/products/products/?ordering=-created_at

# Sort by oldest first
GET /api/v1/products/products/?ordering=created_at

# Sort by name (A-Z)
GET /api/v1/products/products/?ordering=name

# Sort by name (Z-A)
GET /api/v1/products/products/?ordering=-name

# Multiple sorting (price ascending, then name)
GET /api/v1/products/products/?ordering=price,name
```

---

### **9. Pagination**

| Parameter | Type | Description | Default | Example |
|-----------|------|-------------|---------|---------|
| `page` | integer | Page number | 1 | `?page=2` |
| `page_size` | integer | Items per page | 10-100 | `?page_size=20` |

**Examples:**
```bash
# Get page 2
GET /api/v1/products/products/?page=2

# Get 50 items per page
GET /api/v1/products/products/?page_size=50

# Page 3 with 25 items
GET /api/v1/products/products/?page=3&page_size=25
```

---

## 🎯 **Special Endpoints**

### **Featured Products**
```bash
GET /api/v1/products/products/featured/
```
Returns only products marked as featured.

### **In-Stock Products**
```bash
GET /api/v1/products/products/in_stock/
```
Returns only products currently available in stock.

### **Advanced Search**
```bash
GET /api/v1/products/products/search/?q=wireless&category=1&price_min=50
```
Advanced search with multiple filters.

---

## 💡 **Common Use Cases**

### **1. Homepage Featured Products**
```bash
GET /api/v1/products/products/featured/?page_size=8
```

### **2. Category Page**
```bash
GET /api/v1/products/products/?category=1&is_active=true&ordering=-created_at
```

### **3. Price Range Search**
```bash
GET /api/v1/products/products/?price_min=100&price_max=500&in_stock=true
```

### **4. Search with Filters**
```bash
GET /api/v1/products/products/?search=laptop&category=1&price_max=1000&ordering=price
```

### **5. Tag-Based Filtering**
```bash
GET /api/v1/products/products/?tag_names=wireless,bluetooth&in_stock=true
```

### **6. Low Stock Alert (Admin)**
```bash
GET /api/v1/products/products/?low_stock=true&ordering=stock_quantity
```

### **7. New Arrivals**
```bash
GET /api/v1/products/products/?ordering=-created_at&page_size=20
```

### **8. Best Sellers (by name/featured)**
```bash
GET /api/v1/products/products/?is_featured=true&ordering=-created_at
```

---

## 🧪 **Testing in Insomnia**

### **Basic Query**
```
GET http://localhost:8000/api/v1/products/products/
```

### **With Multiple Filters**
```
GET http://localhost:8000/api/v1/products/products/?category=1&price_min=50&price_max=200&in_stock=true&ordering=price
```

### **Search Query**
```
GET http://localhost:8000/api/v1/products/products/?search=wireless&is_active=true
```

### **Featured & Sorted**
```
GET http://localhost:8000/api/v1/products/products/?is_featured=true&ordering=-price&page_size=10
```

---

## 📝 **Parameter Combinations**

You can combine **ANY** of the above parameters! Here are some powerful combinations:

```bash
# Electronics under $200 with stock
/api/v1/products/products/?category_slug=electronics&price_max=200&in_stock=true

# Featured wireless products sorted by price
/api/v1/products/products/?tag_names=wireless&is_featured=true&ordering=price

# Search + Category + Price + Stock + Sort
/api/v1/products/products/?search=headphones&category=1&price_min=50&price_max=150&in_stock=true&ordering=-created_at

# Digital products on sale (featured)
/api/v1/products/products/?is_digital=true&is_featured=true&ordering=price

# Recently added in-stock products
/api/v1/products/products/?in_stock=true&ordering=-created_at&page_size=20
```

---

## ✅ **Response Format**

All list endpoints return paginated responses:

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/products/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "description": "High-quality wireless headphones...",
      "price": "99.99",
      "stock_quantity": 50,
      "is_in_stock": true,
      "is_featured": true,
      "category": {
        "id": 1,
        "name": "Electronics"
      },
      "tags": ["wireless", "audio"],
      "images": [...]
    }
  ]
}
```

---

## 🚀 **Quick Reference**

| Filter Type | Parameters |
|-------------|------------|
| **Search** | `search`, `q`, `name__icontains`, `sku__icontains` |
| **Category** | `category`, `category_slug` |
| **Price** | `price_min`, `price_max`, `price`, `price__gte`, `price__lte` |
| **Stock** | `in_stock`, `low_stock`, `stock_quantity`, `stock_quantity__gte` |
| **Status** | `is_featured`, `is_active`, `is_digital` |
| **Tags** | `tags`, `tag_names` |
| **Date** | `created_after`, `created_before` |
| **Sort** | `ordering` (name, price, created_at, stock_quantity) |
| **Pagination** | `page`, `page_size` |

---

## ❓ **Troubleshooting**

### **"Empty results when filtering"**

#### **Problem: Using `tag_names=electronics` returns empty**
**Solution:** "Electronics" is a **category**, not a tag. Use:
```bash
# Correct - using category
GET /api/v1/products/products/?category_slug=electronics

# Incorrect - "electronics" is not a tag
GET /api/v1/products/products/?tag_names=electronics  ❌
```

#### **Problem: Case sensitivity issues**
**Solution:** 
- Category slugs are **lowercase and hyphenated**
- Tag names are **case-insensitive**
```bash
# Correct
GET /api/v1/products/products/?category_slug=electronics
GET /api/v1/products/products/?category_slug=home-garden

# Incorrect
GET /api/v1/products/products/?category_slug=Electronics  ❌
GET /api/v1/products/products/?category_slug=Home & Garden  ❌
```

#### **Problem: Empty results for parent category**
**Solution:** ✅ **FIXED!** Category filtering now includes subcategories automatically.

When you filter by `category_slug=electronics`, it now returns products from:
- The Electronics category itself (if any)
- ALL subcategories (Smartphones, Laptops, Audio, Gaming, etc.)

Example:
```bash
# Returns 5 products from Electronics and all subcategories
GET /api/v1/products/products/?category_slug=electronics

# Returns only 2 products specifically in Smartphones subcategory
GET /api/v1/products/products/?category_slug=smartphones
```

#### **Problem: "How do I know what categories/tags exist?"**
**Solution:** Query these endpoints first:
```bash
# Get all categories (with parent/child relationships)
GET /api/v1/categories/categories/

# Get all tags
GET /api/v1/products/tags/
```

---

## 📋 **Quick Comparison: Categories vs Tags**

| Feature | Categories | Tags |
|---------|-----------|------|
| **Parameter** | `category` or `category_slug` | `tags` or `tag_names` |
| **Hierarchical** | Yes (parent/subcategories) | No (flat list) |
| **Case Sensitive** | Yes (slugs are lowercase) | No |
| **Examples** | Electronics, Clothing, Books | wireless, bluetooth, premium |
| **List Endpoint** | `/api/v1/categories/categories/` | `/api/v1/products/tags/` |
| **Product Relationship** | One category per product | Multiple tags per product |

---

## 🎯 **Real-World Examples**

### **"Show me wireless headphones under $100"**
```bash
# Use category (Audio) + tag (wireless) + price
GET /api/v1/products/products/?category_slug=audio&tag_names=wireless&price_max=100
```

### **"Show me all Electronics"**
```bash
# Use category, not tag
GET /api/v1/products/products/?category_slug=electronics
```

### **"Show me products tagged as 'premium'"**
```bash
# Use tag_names
GET /api/v1/products/products/?tag_names=premium
```

### **"Show me laptops in Electronics category"**
```bash
# Use subcategory
GET /api/v1/products/products/?category_slug=laptops
```

---

That's it! You now have all possible filters and parameters for the products endpoint. Happy testing! 🎉