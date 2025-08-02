# 🔗 Bazary Database Relationships

**Last Updated:** August 2, 2025  
**Purpose:** Detailed documentation of all database relationships, constraints, and dependencies

---

## 🌐 Relationship Overview

The Bazary database follows a normalized design with clear relationships between entities. All relationships use Django's ORM conventions with proper foreign keys and constraints.

### 📊 Relationship Summary

| Relationship Type | Count | Examples |
|-------------------|-------|----------|
| One-to-Many | 4 | User → Products, Category → Products |
| Many-to-Many | 1 | Products ↔ Tags |
| Self-Referencing | 1 | Category → Parent Category |
| Polymorphic | 0 | None currently |

---

## 🏗️ Detailed Relationships

### 1. User → Products (One-to-Many)

**Relationship:** `User.products` ← `Product.created_by`

```python
# Model Definition
class Product(models.Model):
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,  # Prevent user deletion if they have products
        related_name='products',
        help_text="User who created this product"
    )
```

**Database Schema:**
```sql
ALTER TABLE products 
ADD CONSTRAINT fk_products_created_by 
FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE RESTRICT;
```

**Business Rules:**
- ✅ **Users can create multiple products**
- ✅ **Products must have a creator (NOT NULL)**
- ❌ **Cannot delete user if they have products (PROTECT)**
- ✅ **Staff and admin users can create products**
- ❌ **Regular customers cannot create products (enforced in views)**

**Usage Examples:**
```python
# Get all products created by a user
user = User.objects.get(username='admin')
user_products = user.products.filter(is_active=True)

# Get product creator
product = Product.objects.get(slug='iphone-15-pro')
creator = product.created_by
print(f"Created by: {creator.get_full_name()}")

# Query optimization
products_with_creators = Product.objects.select_related('created_by')
```

**Performance Notes:**
- Index on `created_by_id` for fast user-based filtering
- Use `select_related('created_by')` to avoid N+1 queries
- Consider pagination for users with many products

---

### 2. Category → Products (One-to-Many)

**Relationship:** `Category.products` ← `Product.category`

```python
# Model Definition
class Product(models.Model):
    category = models.ForeignKey(
        'catalog.Category',
        on_delete=models.PROTECT,  # Prevent category deletion if it has products
        related_name='products',
        help_text="Product category"
    )
```

**Database Schema:**
```sql
ALTER TABLE products 
ADD CONSTRAINT fk_products_category 
FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
```

**Business Rules:**
- ✅ **Categories can have multiple products**
- ✅ **Products must belong to a category (NOT NULL)**
- ❌ **Cannot delete category if it has products (PROTECT)**
- ✅ **Can move products between categories by updating category_id**
- ✅ **Child categories can have products directly**

**Usage Examples:**
```python
# Get all products in a category
category = Category.objects.get(slug='smartphones')
products_in_category = category.products.filter(is_active=True)

# Get products in category and subcategories
def get_category_products_recursive(category):
    # Get all descendant categories
    descendants = category.get_descendants(include_self=True)
    return Product.objects.filter(
        category__in=descendants,
        is_active=True
    )

# Product's category info
product = Product.objects.get(slug='iphone-15-pro')
category_path = product.category.get_path()
```

**Performance Notes:**
- Composite index on `(category_id, is_active)` for filtering
- Use `select_related('category')` for product lists
- Consider denormalized category paths for deep hierarchies

---

### 3. Category → Parent Category (Self-Referencing)

**Relationship:** `Category.children` ← `Category.parent`

```python
# Model Definition
class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,  # Delete children when parent is deleted
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category"
    )
```

**Database Schema:**
```sql
ALTER TABLE categories 
ADD CONSTRAINT fk_categories_parent 
FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE;
```

**Business Rules:**
- ✅ **Categories can have unlimited nesting depth**
- ✅ **Root categories have `parent=NULL`**
- ✅ **Deleting parent deletes all children (CASCADE)**
- ❌ **Categories cannot be their own parent (prevent cycles)**
- ✅ **Categories can be moved between parents**

**Hierarchy Examples:**
```
Electronics (parent=NULL)
├── Smartphones (parent=Electronics)
│   ├── iPhone (parent=Smartphones)
│   └── Samsung (parent=Smartphones)
├── Laptops (parent=Electronics)
│   ├── Gaming Laptops (parent=Laptops)
│   └── Business Laptops (parent=Laptops)
└── Accessories (parent=Electronics)

Clothing (parent=NULL)
├── Men's Clothing (parent=Clothing)
└── Women's Clothing (parent=Clothing)
```

**Usage Examples:**
```python
# Get root categories
root_categories = Category.objects.filter(parent=None, is_active=True)

# Get category tree
def build_category_tree(parent=None):
    categories = Category.objects.filter(parent=parent, is_active=True)
    tree = []
    for category in categories:
        children = build_category_tree(category)
        tree.append({
            'category': category,
            'children': children
        })
    return tree

# Get category breadcrumbs
def get_breadcrumbs(category):
    breadcrumbs = []
    current = category
    while current:
        breadcrumbs.insert(0, current)
        current = current.parent
    return breadcrumbs

# Move category to new parent
category = Category.objects.get(slug='gaming-laptops')
new_parent = Category.objects.get(slug='electronics')
category.parent = new_parent
category.save()
```

**Performance Notes:**
- Index on `parent_id` for hierarchy queries
- Consider using django-mptt for complex tree operations
- Cache category trees for menu generation
- Limit tree depth to prevent performance issues

---

### 4. Product → Product Images (One-to-Many)

**Relationship:** `Product.images` ← `ProductImage.product`

```python
# Model Definition
class ProductImage(models.Model):
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,  # Delete images when product is deleted
        related_name='images',
        help_text="Associated product"
    )
```

**Database Schema:**
```sql
ALTER TABLE product_images 
ADD CONSTRAINT fk_product_images_product 
FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
```

**Business Rules:**
- ✅ **Products can have multiple images**
- ✅ **Only one image can be primary per product**
- ✅ **Deleting product deletes all images (CASCADE)**
- ✅ **Images are ordered by `sort_order` field**
- ❌ **Products don't require images (optional)**

**Usage Examples:**
```python
# Get product with images
product = Product.objects.prefetch_related('images').get(slug='iphone-15-pro')
primary_image = product.images.filter(is_primary=True).first()
all_images = product.images.order_by('sort_order')

# Add image to product
ProductImage.objects.create(
    product=product,
    image='products/iphone-15-pro-2.jpg',
    alt_text='iPhone 15 Pro side view',
    sort_order=1
)

# Set primary image
new_primary = product.images.first()
# Clear current primary
product.images.update(is_primary=False)
# Set new primary
new_primary.is_primary = True
new_primary.save()
```

**Performance Notes:**
- Composite index on `(product_id, is_primary)` for primary image lookups
- Use `prefetch_related('images')` for product lists
- Consider image optimization and CDN for performance

---

### 5. Products ↔ Tags (Many-to-Many)

**Relationship:** `Product.tags` ↔ `Tag.products`

```python
# Model Definition
class Product(models.Model):
    tags = models.ManyToManyField(
        'catalog.Tag',
        blank=True,
        related_name='products',
        help_text="Product tags"
    )
```

**Database Schema:**
```sql
-- Junction table created automatically by Django
CREATE TABLE products_tags (
    id BIGINT PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    tag_id BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(product_id, tag_id)
);
```

**Business Rules:**
- ✅ **Products can have multiple tags**
- ✅ **Tags can be applied to multiple products**
- ✅ **Tags are optional for products**
- ✅ **No limit on number of tags per product**
- ✅ **Deleting product removes tag associations**
- ✅ **Deleting tag removes product associations**

**Usage Examples:**
```python
# Add tags to product
product = Product.objects.get(slug='iphone-15-pro')
new_tag = Tag.objects.get(slug='new')
popular_tag = Tag.objects.get(slug='popular')

product.tags.add(new_tag, popular_tag)

# Get products with specific tag
new_products = Product.objects.filter(tags__slug='new', is_active=True)

# Get all tags for a product
product_tags = product.tags.all()

# Remove tag from product
product.tags.remove(new_tag)

# Get products with multiple tags (AND)
premium_electronics = Product.objects.filter(
    tags__slug='premium'
).filter(
    tags__slug='electronics'
).distinct()

# Get products with any of multiple tags (OR)
featured_or_new = Product.objects.filter(
    tags__slug__in=['featured', 'new']
).distinct()
```

**Performance Notes:**
- Indexes on junction table for fast lookups
- Use `prefetch_related('tags')` for product lists
- Consider tag popularity caching
- Use `distinct()` when filtering by tags to avoid duplicates

---

## 📈 Relationship Performance Optimization

### Query Optimization Patterns

**1. Eager Loading (Prevent N+1 Queries):**
```python
# Good: Load related data in one query
products = Product.objects.select_related('category', 'created_by').prefetch_related('tags', 'images')

# Bad: Causes N+1 queries
products = Product.objects.all()
for product in products:
    print(product.category.name)  # Additional query per product
```

**2. Efficient Filtering:**
```python
# Good: Use database-level filtering
active_products = Product.objects.filter(is_active=True, category__is_active=True)

# Bad: Filter in Python
all_products = Product.objects.all()
active_products = [p for p in all_products if p.is_active and p.category.is_active]
```

**3. Complex Queries:**
```python
# Get categories with product counts
categories_with_counts = Category.objects.annotate(
    product_count=Count('products', filter=Q(products__is_active=True))
).filter(is_active=True)

# Get popular tags (most used)
popular_tags = Tag.objects.annotate(
    usage_count=Count('products')
).order_by('-usage_count')[:10]
```

### Index Strategy

**Primary Indexes (Automatically created):**
- `users_pkey` on `users.id`
- `categories_pkey` on `categories.id`  
- `products_pkey` on `products.id`
- `product_images_pkey` on `product_images.id`
- `tags_pkey` on `tags.id`

**Foreign Key Indexes:**
- `products_created_by_id_idx` on `products.created_by_id`
- `products_category_id_idx` on `products.category_id`
- `product_images_product_id_idx` on `product_images.product_id`
- `categories_parent_id_idx` on `categories.parent_id`

**Composite Indexes (Recommended):**
```sql
-- Product filtering
CREATE INDEX products_category_active_idx ON products(category_id, is_active);
CREATE INDEX products_active_featured_idx ON products(is_active, is_featured);
CREATE INDEX products_active_created_idx ON products(is_active, created_at DESC);

-- Category hierarchy
CREATE INDEX categories_parent_active_sort_idx ON categories(parent_id, is_active, sort_order);

-- Product images
CREATE INDEX product_images_product_primary_idx ON product_images(product_id, is_primary);
```

---

## 🔒 Relationship Constraints & Integrity

### Foreign Key Constraints

**PROTECT Constraints (Prevent deletion):**
- `products.created_by_id` → `users.id` (Cannot delete users with products)
- `products.category_id` → `categories.id` (Cannot delete categories with products)

**CASCADE Constraints (Automatic deletion):**
- `categories.parent_id` → `categories.id` (Delete children with parent)
- `product_images.product_id` → `products.id` (Delete images with product)
- `products_tags.product_id` → `products.id` (Remove tag associations)
- `products_tags.tag_id` → `tags.id` (Remove product associations)

### Data Integrity Rules

**Business Logic Constraints:**
```python
# Enforce in Django models and admin
class ProductAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Only staff can create products
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can create products")
        
        # Ensure category is active
        if not obj.category.is_active:
            raise ValidationError("Cannot assign product to inactive category")
        
        super().save_model(request, obj, form, change)
```

**Database-Level Constraints:**
```sql
-- Positive prices
ALTER TABLE products ADD CONSTRAINT positive_price CHECK (price >= 0);
ALTER TABLE products ADD CONSTRAINT positive_compare_price CHECK (compare_price >= 0);

-- Valid stock quantities
ALTER TABLE products ADD CONSTRAINT non_negative_stock CHECK (stock_quantity >= 0);

-- Primary image uniqueness per product
CREATE UNIQUE INDEX product_primary_image_unique 
ON product_images(product_id) 
WHERE is_primary = true;
```

---

## 🔄 Relationship Migration Patterns

### Adding New Relationships

**1. Adding Optional Foreign Key:**
```python
# Migration example
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(
                'catalog.Brand',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='products'
            ),
        ),
    ]
```

**2. Adding Required Foreign Key:**
```python
# Two-step migration for existing data
# Step 1: Add nullable field
migrations.AddField(
    model_name='product',
    name='supplier',
    field=models.ForeignKey(
        'catalog.Supplier',
        on_delete=models.PROTECT,
        null=True  # Temporarily nullable
    ),
)

# Step 2: Set default values and make required
# (Requires data migration to set supplier for existing products)
```

### Changing Relationship Types

**From ForeignKey to ManyToMany:**
```python
# 1. Create new M2M field
# 2. Data migration to populate relationships
# 3. Remove old ForeignKey field
# 4. Rename new field to replace old one
```

This relationship documentation provides a comprehensive understanding of how all entities in the Bazary database are connected and how to work with them efficiently.
