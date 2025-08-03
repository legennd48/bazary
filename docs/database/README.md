# 🗄️ Bazary Database Documentation

**Complete database schema documentation for the Bazary e-commerce platform**

---

## 📚 Documentation Overview

This directory contains comprehensive documentation for the Bazary database schema, relationships, and data management.

### 📄 Available Documents

| Document | Purpose | Audience |
|----------|---------|----------|
| [`schema.md`](schema.md) | Complete database schema with tables, fields, and business rules | Developers, DBAs |
| [`relationships.md`](relationships.md) | Detailed relationship documentation with examples | Developers, System Architects |
| [`data_dictionary.md`](data_dictionary.md) | Field-by-field documentation with validation rules | Developers, QA Engineers |
| [`bazary_schema.dbml`](bazary_schema.dbml) | Visual database diagram for dbdiagram.io | All stakeholders |

---

## 🗃️ Database Quick Reference

### Core Tables

| Table | Records | Purpose |
|-------|---------|---------|
| `users` | ~10-100K | User authentication & profiles |
| `categories` | ~50-200 | Hierarchical product organization |
| `products` | ~1K-100K | Product catalog |
| `product_images` | ~5K-500K | Product media |
| `tags` | ~50-500 | Product labeling |

### Key Relationships

```
User (1) ────────> (*) Product (created_by)
Category (1) ────> (*) Product  
Category (1) ────> (*) Category (parent/child)
Product (*) ─────> (*) Tag (many-to-many)
Product (1) ─────> (*) ProductImage
```

---

## 🚀 Quick Start

### 1. View Database Schema Visually

Visit [dbdiagram.io](https://dbdiagram.io/d) and paste the contents of [`bazary_schema.dbml`](bazary_schema.dbml) to see an interactive database diagram.

### 2. Seed Development Data

```bash
# Seed database with realistic test data
python manage.py seed_database --verbose

# Options:
python manage.py seed_database --users=20 --products=50  # Custom quantities
python manage.py seed_database --reset                  # Reset before seeding
python manage.py seed_database --users-only             # Only create users
```

### 3. Common Database Operations

```python
# Get products with category and creator
products = Product.objects.select_related('category', 'created_by')

# Get category hierarchy
root_categories = Category.objects.filter(parent=None)

# Get products with tags
products_with_tags = Product.objects.prefetch_related('tags')

# Search products
search_results = Product.objects.filter(
    name__icontains='search_term',
    is_active=True
)
```

---

## 📊 Database Schema Summary

### Users & Authentication

- **UUID-based user identification** for enhanced security
- **Role-based access control** (admin, staff, customer)
- **Email verification system** for account security
- **Soft delete patterns** for data preservation

### Product Catalog

- **Hierarchical categories** with unlimited nesting depth
- **Comprehensive product model** with pricing, inventory, SEO
- **Multi-image support** with primary image designation
- **Flexible tagging system** for product attributes

### Performance Features

- **Optimized indexes** for common query patterns
- **Composite indexes** for filtering combinations
- **Efficient relationship queries** with proper foreign keys
- **Scalable design** supporting 100K+ products

---

## 🔧 Database Management

### Seeding Command Features

The `seed_database` management command provides:

- **Realistic test data** with proper relationships
- **Configurable quantities** for different environments
- **Hierarchical categories** (Electronics, Clothing, Books, etc.)
- **Diverse product types** with realistic pricing and descriptions
- **User roles** (admin, staff, customers) with proper permissions
- **Product tags** for filtering and categorization

### Data Quality

After seeding, you'll have:

- **18 Users**: 1 admin, 1 staff, 16 customers
- **25 Categories**: 5 parent categories with 4 subcategories each
- **10 Tags**: New, Popular, Sale, Premium, etc.
- **26 Products**: Diverse products across all categories
- **Proper relationships**: All foreign keys and many-to-many relationships populated

---

## 🎯 Performance Optimization

### Index Strategy

**Primary Indexes:**
- All primary keys (automatic)
- Foreign key relationships
- Unique constraints (slugs, SKUs)

**Composite Indexes:**
- `(category_id, is_active)` - Product filtering
- `(is_active, is_featured)` - Featured products
- `(parent_id, is_active, sort_order)` - Category hierarchy

### Query Patterns

**Efficient Loading:**
```python
# Good: Eager loading
products = Product.objects.select_related('category').prefetch_related('tags')

# Bad: N+1 queries
for product in Product.objects.all():
    print(product.category.name)  # Additional query per product
```

**Complex Queries:**
```python
# Category with product counts
categories = Category.objects.annotate(
    product_count=Count('products', filter=Q(products__is_active=True))
)

# Popular tags
popular_tags = Tag.objects.annotate(
    usage_count=Count('products')
).order_by('-usage_count')
```

---

## 🔒 Data Integrity

### Foreign Key Constraints

- **PROTECT**: Prevent deletion of users/categories with dependent records
- **CASCADE**: Automatic cleanup of images when products deleted
- **Referential integrity** enforced at database level

### Business Rules

- Only staff users can create products
- Categories with products cannot be deleted
- Primary image uniqueness per product
- Positive prices and stock quantities
- Unique slugs and SKUs across platform

---

## 📈 Scalability Considerations

### Current Capacity

- **Users**: Efficiently handles 100K+ users
- **Products**: Optimized for 100K+ products
- **Categories**: Supports deep hierarchical nesting
- **Images**: CDN-ready structure for unlimited images

### Future Optimizations

1. **Table Partitioning**: For large product datasets
2. **Caching Layer**: Redis for frequently accessed data
3. **Search Engine**: Elasticsearch integration
4. **CDN Integration**: Optimized image delivery

---

## 🛠️ Development Workflow

### Database Changes

1. **Create migration**: `python manage.py makemigrations`
2. **Review migration**: Check generated SQL and logic
3. **Apply migration**: `python manage.py migrate`
4. **Update documentation**: Reflect changes in schema docs
5. **Update seeding**: Modify seed_database command if needed

### Testing Data

```bash
# Reset and create fresh test data
python manage.py seed_database --reset --verbose

# Create additional products for testing
python manage.py seed_database --products=100

# Create more users for load testing
python manage.py seed_database --users=50
```

---

## 📞 Support & Maintenance

### Common Issues

**Migration Problems:**
- Ensure proper foreign key relationships
- Check for data consistency before applying
- Use data migrations for complex changes

**Performance Issues:**
- Verify proper index usage with `EXPLAIN ANALYZE`
- Use `select_related` and `prefetch_related` appropriately
- Monitor query execution times

**Data Integrity:**
- Regular database backups
- Constraint validation
- Orphaned record cleanup

### Monitoring

- **Query Performance**: Django Debug Toolbar
- **Database Size**: Regular monitoring of table sizes
- **Index Usage**: PostgreSQL query statistics
- **Relationship Integrity**: Regular constraint validation

---

## 📋 Maintenance Checklist

### Weekly
- [ ] Review slow query logs
- [ ] Check database size growth
- [ ] Validate data integrity constraints

### Monthly
- [ ] Update database statistics
- [ ] Review index usage patterns
- [ ] Cleanup orphaned records
- [ ] Update documentation if schema changed

### Quarterly
- [ ] Performance analysis and optimization
- [ ] Backup and recovery testing
- [ ] Schema evolution planning
- [ ] Capacity planning review

---

This documentation provides a complete reference for understanding, maintaining, and optimizing the Bazary database schema. For specific implementation details, refer to the individual documentation files in this directory.
