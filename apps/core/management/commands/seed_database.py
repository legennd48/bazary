"""
Django management command to seed the database with realistic test data.
"""

import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from apps.categories.models import Category
from apps.products.models import Product, ProductImage, Tag

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Seed database with realistic test data for development and testing.
    
    Usage:
        python manage.py seed_database
        python manage.py seed_database --reset  # Clear existing data first
        python manage.py seed_database --users-only  # Only create users
        python manage.py seed_database --products=50  # Specify number of products
    """
    
    help = 'Seed database with realistic test data'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--users-only',
            action='store_true',
            help='Only create user accounts',
        )
        parser.add_argument(
            '--categories-only',
            action='store_true',
            help='Only create categories',
        )
        parser.add_argument(
            '--products-only',
            action='store_true',
            help='Only create products',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create (default: 10)',
        )
        parser.add_argument(
            '--products',
            type=int,
            default=25,
            help='Number of products to create (default: 25)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        """Execute the seeding process."""
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS('🌱 Starting database seeding...')
        )
        
        if options['verbose']:
            self.stdout.write('Configuration:')
            self.stdout.write(f"  - Users: {options['users']}")
            self.stdout.write(f"  - Products: {options['products']}")
            self.stdout.write(f"  - Reset data: {options['reset']}")
        
        try:
            with transaction.atomic():
                if options['reset']:
                    self.clear_existing_data()
                
                if not options['categories_only'] and not options['products_only']:
                    self.create_users(options['users'], options['verbose'])
                
                if not options['users_only'] and not options['products_only']:
                    self.create_categories(options['verbose'])
                    self.create_tags(options['verbose'])
                
                if not options['users_only'] and not options['categories_only']:
                    self.create_products(options['products'], options['verbose'])
                
                self.display_summary()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Seeding failed: {str(e)}')
            )
            raise
        
        duration = timezone.now() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Database seeding completed in {duration.total_seconds():.2f} seconds!'
            )
        )
    
    def clear_existing_data(self):
        """Clear existing seeded data."""
        self.stdout.write('🗑️ Clearing existing data...')
        
        # Clear products and related data
        Product.objects.all().delete()
        ProductImage.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        
        # Clear non-admin users
        User.objects.filter(is_superuser=False, is_staff=False).delete()
        
        self.stdout.write(self.style.WARNING('✅ Existing data cleared'))
    
    def create_users(self, count, verbose=False):
        """Create test users with different roles."""
        if verbose:
            self.stdout.write(f'👥 Creating {count} users...')
        
        users_created = 0
        
        # Create admin user if doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@bazary.com',
                password='admin123!',
                first_name='Admin',
                last_name='User'
            )
            users_created += 1
            if verbose:
                self.stdout.write(f'  ✓ Created admin user: {admin_user.username}')
        
        # Create staff user
        if not User.objects.filter(username='staff').exists():
            staff_user = User.objects.create_user(
                username='staff',
                email='staff@bazary.com',
                password='staff123!',
                first_name='Staff',
                last_name='Member',
                is_staff=True
            )
            users_created += 1
            if verbose:
                self.stdout.write(f'  ✓ Created staff user: {staff_user.username}')
        
        # Create regular customers
        customers = [
            {
                'username': 'john_doe',
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '+1234567890'
            },
            {
                'username': 'jane_smith',
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone_number': '+1234567891'
            },
            {
                'username': 'bob_wilson',
                'email': 'bob.wilson@example.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'phone_number': '+1234567892'
            },
            {
                'username': 'alice_brown',
                'email': 'alice.brown@example.com',
                'first_name': 'Alice',
                'last_name': 'Brown',
                'phone_number': '+1234567893'
            },
            {
                'username': 'charlie_davis',
                'email': 'charlie.davis@example.com',
                'first_name': 'Charlie',
                'last_name': 'Davis',
                'phone_number': '+1234567894'
            },
        ]
        
        for i, customer_data in enumerate(customers[:count-2]):  # -2 for admin and staff
            if not User.objects.filter(username=customer_data['username']).exists():
                user = User.objects.create_user(
                    username=customer_data['username'],
                    email=customer_data['email'],
                    password='customer123!',
                    first_name=customer_data['first_name'],
                    last_name=customer_data['last_name'],
                    phone_number=customer_data.get('phone_number', ''),
                    is_verified=True
                )
                users_created += 1
                if verbose:
                    self.stdout.write(f'  ✓ Created customer: {user.username}')
        
        # Create additional generic users if needed
        existing_users = User.objects.count()
        remaining = max(0, count - existing_users)
        
        for i in range(remaining):
            username = f'user{existing_users + i + 1}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='user123!',
                    first_name=f'User',
                    last_name=f'{existing_users + i + 1}',
                    is_verified=True
                )
                users_created += 1
                if verbose:
                    self.stdout.write(f'  ✓ Created user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created {users_created} users')
        )
    
    def create_categories(self, verbose=False):
        """Create realistic product categories."""
        if verbose:
            self.stdout.write('🗂️ Creating categories...')
        
        categories_data = [
            # Electronics
            {
                'name': 'Electronics',
                'description': 'Electronic devices and gadgets',
                'subcategories': [
                    {'name': 'Smartphones', 'description': 'Mobile phones and accessories'},
                    {'name': 'Laptops', 'description': 'Portable computers and accessories'},
                    {'name': 'Audio', 'description': 'Headphones, speakers, and audio equipment'},
                    {'name': 'Gaming', 'description': 'Gaming consoles and accessories'},
                ]
            },
            # Clothing
            {
                'name': 'Clothing',
                'description': 'Fashion and apparel',
                'subcategories': [
                    {'name': 'Men\'s Clothing', 'description': 'Clothing for men'},
                    {'name': 'Women\'s Clothing', 'description': 'Clothing for women'},
                    {'name': 'Shoes', 'description': 'Footwear for all occasions'},
                    {'name': 'Accessories', 'description': 'Fashion accessories'},
                ]
            },
            # Home & Garden
            {
                'name': 'Home & Garden',
                'description': 'Home improvement and garden supplies',
                'subcategories': [
                    {'name': 'Furniture', 'description': 'Home and office furniture'},
                    {'name': 'Kitchen', 'description': 'Kitchen appliances and tools'},
                    {'name': 'Garden', 'description': 'Gardening tools and supplies'},
                    {'name': 'Decor', 'description': 'Home decoration items'},
                ]
            },
            # Books
            {
                'name': 'Books',
                'description': 'Books and educational materials',
                'subcategories': [
                    {'name': 'Fiction', 'description': 'Novels and fiction books'},
                    {'name': 'Non-Fiction', 'description': 'Educational and informational books'},
                    {'name': 'Technology', 'description': 'Programming and technology books'},
                    {'name': 'Business', 'description': 'Business and entrepreneurship books'},
                ]
            },
            # Sports & Outdoors
            {
                'name': 'Sports & Outdoors',
                'description': 'Sports equipment and outdoor gear',
                'subcategories': [
                    {'name': 'Fitness', 'description': 'Fitness equipment and gear'},
                    {'name': 'Outdoor', 'description': 'Camping and outdoor activities'},
                    {'name': 'Team Sports', 'description': 'Equipment for team sports'},
                ]
            }
        ]
        
        categories_created = 0
        
        for cat_data in categories_data:
            # Create parent category
            parent_cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True,
                    'sort_order': categories_created * 10
                }
            )
            
            if created:
                categories_created += 1
                if verbose:
                    self.stdout.write(f'  ✓ Created category: {parent_cat.name}')
            
            # Create subcategories
            for i, subcat_data in enumerate(cat_data.get('subcategories', [])):
                subcat, created = Category.objects.get_or_create(
                    name=subcat_data['name'],
                    defaults={
                        'description': subcat_data['description'],
                        'parent': parent_cat,
                        'is_active': True,
                        'sort_order': i * 10
                    }
                )
                
                if created:
                    categories_created += 1
                    if verbose:
                        self.stdout.write(f'    ✓ Created subcategory: {subcat.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created {categories_created} categories')
        )
    
    def create_tags(self, verbose=False):
        """Create product tags."""
        if verbose:
            self.stdout.write('🏷️ Creating tags...')
        
        tags_data = [
            {'name': 'New', 'color': '#28a745'},
            {'name': 'Popular', 'color': '#007bff'},
            {'name': 'Sale', 'color': '#dc3545'},
            {'name': 'Limited Edition', 'color': '#6f42c1'},
            {'name': 'Best Seller', 'color': '#fd7e14'},
            {'name': 'Premium', 'color': '#6c757d'},
            {'name': 'Eco-Friendly', 'color': '#20c997'},
            {'name': 'Handmade', 'color': '#e83e8c'},
            {'name': 'Vintage', 'color': '#795548'},
            {'name': 'Trending', 'color': '#ff5722'},
        ]
        
        tags_created = 0
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'color': tag_data['color']
                }
            )
            
            if created:
                tags_created += 1
                if verbose:
                    self.stdout.write(f'  ✓ Created tag: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created {tags_created} tags')
        )
    
    def create_products(self, count, verbose=False):
        """Create realistic products."""
        if verbose:
            self.stdout.write(f'📦 Creating {count} products...')
        
        # Get necessary objects
        categories = list(Category.objects.filter(parent__isnull=False))  # Only subcategories
        tags = list(Tag.objects.all())
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not categories:
            self.stdout.write(
                self.style.ERROR('❌ No categories found. Create categories first.')
            )
            return
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('❌ No admin user found. Create users first.')
            )
            return
        
        # Sample products for different categories
        products_templates = {
            'smartphones': [
                {'name': 'iPhone 15 Pro', 'price': 999.99, 'description': 'Latest iPhone with advanced features'},
                {'name': 'Samsung Galaxy S24', 'price': 899.99, 'description': 'Premium Android smartphone'},
                {'name': 'Google Pixel 8', 'price': 699.99, 'description': 'Google\'s flagship smartphone'},
            ],
            'laptops': [
                {'name': 'MacBook Pro 16"', 'price': 2399.99, 'description': 'Professional laptop for creators'},
                {'name': 'Dell XPS 13', 'price': 1299.99, 'description': 'Ultrabook with premium design'},
                {'name': 'ThinkPad X1 Carbon', 'price': 1799.99, 'description': 'Business laptop with durability'},
            ],
            'audio': [
                {'name': 'AirPods Pro', 'price': 249.99, 'description': 'Wireless earbuds with noise cancellation'},
                {'name': 'Sony WH-1000XM4', 'price': 349.99, 'description': 'Premium noise-canceling headphones'},
                {'name': 'Bose QuietComfort', 'price': 329.99, 'description': 'Comfortable wireless headphones'},
            ],
            'men\'s clothing': [
                {'name': 'Classic Blue Jeans', 'price': 79.99, 'description': 'Comfortable denim jeans'},
                {'name': 'Cotton T-Shirt Pack', 'price': 29.99, 'description': 'Set of 3 basic t-shirts'},
                {'name': 'Wool Sweater', 'price': 89.99, 'description': 'Warm winter sweater'},
            ],
            'women\'s clothing': [
                {'name': 'Summer Dress', 'price': 59.99, 'description': 'Light and breezy summer dress'},
                {'name': 'Yoga Leggings', 'price': 39.99, 'description': 'High-quality athletic leggings'},
                {'name': 'Silk Blouse', 'price': 129.99, 'description': 'Elegant silk blouse'},
            ],
            'books': [
                {'name': 'Python Programming Guide', 'price': 49.99, 'description': 'Comprehensive Python tutorial'},
                {'name': 'Digital Marketing Handbook', 'price': 34.99, 'description': 'Modern marketing strategies'},
                {'name': 'Science Fiction Novel', 'price': 14.99, 'description': 'Exciting sci-fi adventure'},
            ],
            'furniture': [
                {'name': 'Modern Office Chair', 'price': 299.99, 'description': 'Ergonomic office chair'},
                {'name': 'Coffee Table', 'price': 199.99, 'description': 'Stylish living room table'},
                {'name': 'Bookshelf', 'price': 149.99, 'description': '5-tier wooden bookshelf'},
            ],
        }
        
        products_created = 0
        
        # Create products based on templates
        for i in range(count):
            # Select a category
            category = categories[i % len(categories)]
            category_key = category.name.lower()
            
            # Find matching template or use generic
            templates = products_templates.get(category_key, [
                {'name': f'Product {i+1}', 'price': 99.99, 'description': f'Quality product in {category.name}'}
            ])
            
            template = templates[i % len(templates)]
            
            # Modify name to make it unique
            product_name = f"{template['name']} - Model {i+1}"
            
            # Create product
            product = Product.objects.create(
                name=product_name,
                description=template['description'],
                short_description=template['description'][:100],
                price=Decimal(str(template['price'])),
                compare_price=Decimal(str(template['price'] + 50.00)) if i % 3 == 0 else None,
                category=category,
                stock_quantity=50 + (i % 100),
                low_stock_threshold=10,
                is_active=True,
                is_featured=i % 5 == 0,  # Every 5th product is featured
                is_digital=category.name in ['Books'] and i % 4 == 0,  # Some books are digital
                track_inventory=True,
                created_by=admin_user
            )
            
            # Add tags (1-3 random tags per product)
            import random
            product_tags = random.sample(tags, min(random.randint(1, 3), len(tags)))
            product.tags.set(product_tags)
            
            products_created += 1
            
            if verbose and products_created % 10 == 0:
                self.stdout.write(f'  ✓ Created {products_created} products...')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created {products_created} products')
        )
    
    def display_summary(self):
        """Display seeding summary."""
        self.stdout.write('\n📊 Seeding Summary:')
        self.stdout.write(f'  👥 Users: {User.objects.count()}')
        self.stdout.write(f'  🗂️ Categories: {Category.objects.count()}')
        self.stdout.write(f'  🏷️ Tags: {Tag.objects.count()}')
        self.stdout.write(f'  📦 Products: {Product.objects.count()}')
        self.stdout.write(f'  🖼️ Product Images: {ProductImage.objects.count()}')
        
        # Show featured products
        featured_count = Product.objects.filter(is_featured=True).count()
        self.stdout.write(f'  ⭐ Featured Products: {featured_count}')
        
        # Show out of stock products
        out_of_stock = Product.objects.filter(stock_quantity=0).count()
        self.stdout.write(f'  📭 Out of Stock: {out_of_stock}')
