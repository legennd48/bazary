# 🛒 Bazary - Advanced E-Commerce Backend Platform

[![CI/CD Pipeline](https://github.com/legennd48/bazary/workflows/CI%20Pipeline/badge.svg)](https://github.com/legennd48/bazary/actions)
[![Code Coverage](https://codecov.io/gh/legennd48/bazary/branch/main/graph/badge.svg)](https://codecov.io/gh/legennd48/bazary)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A sophisticated, production-ready Django e-commerce platform with advanced payment processing, shopping cart functionality, and comprehensive product variant system**

Bazary is a feature-rich, enterprise-grade e-commerce backend that goes beyond basic product management. It includes complete payment processing with multiple gateway support, advanced shopping cart functionality, product variants system, and comprehensive user management - all built with production-ready DevOps practices.

## ✨ Key Features

🛍️ **Advanced E-Commerce Core**
- **Product Variants System**: Size, color, material options with individual pricing and stock
- **Multi-Provider Payment Processing**: Chapa (Ethiopian), Stripe, PayPal integration
- **Shopping Cart System**: Persistent carts with real-time calculations and stock validation
- **Advanced Product Management**: Full catalog with images, categories, tags, and variants
- **Transaction Management**: Complete payment lifecycle with webhooks and verification

🔐 **Advanced Authentication & Security**
- **Extended User System**: Custom profiles, addresses, and verification system
- **JWT Authentication**: Access/refresh tokens with role-based permissions
- **Security Features**: CSRF protection, secure payment handling, rate limiting
- **User Roles**: Admin, staff, customer roles with granular permissions

🛒 **Shopping Experience**
- **Cart Management**: Add, update, remove items with real-time totals
- **Guest Cart Support**: Session-based carts for non-authenticated users
- **Price Calculations**: Automatic subtotal, tax, shipping calculations
- **Stock Validation**: Real-time inventory checking during checkout
- **Payment Processing**: Multi-gateway payment with transaction tracking

🚀 **DevOps Excellence**
- **Complete CI/CD Pipeline**: GitHub Actions with automated testing and deployment
- **Docker Containerization**: Development and production-ready containers
- **Git Flow Workflow**: Feature branching with automated quality checks
- **Multi-Environment Support**: Development, staging, production configurations
- **Database Optimization**: PostgreSQL with Redis caching and performance indexing

🔒 **Security & Performance**
- **Payment Security**: PCI DSS ready with secure token handling
- **Database Optimization**: Query optimization with select_related and prefetch_related
- **Comprehensive Indexing**: Performance-optimized database indexes
- **Rate Limiting**: API throttling and abuse prevention
- **Monitoring Ready**: Comprehensive logging and error tracking

📚 **Developer Experience**
- **Comprehensive API Documentation**: Swagger/OpenAPI with live examples
- **Pre-commit Hooks**: Black, isort, flake8 for code quality
- **Extensive Testing**: 80%+ test coverage with pytest and factory-boy
- **Type Hints**: Full type annotation for better IDE support
- **Complete Documentation**: Setup guides, API docs, and deployment guides

## 🚀 Quick Start

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for production deployment)

### 1. Clone and Setup

```bash
git clone https://github.com/legennd48/bazary.git
cd bazary
cp .env.example .env.dev
```

### 2. Start Development Environment

```bash
# Start all services
docker-compose up --build

# In a new terminal, run migrations
### 2. Start Development Environment

```bash
# Start all services (API runs on port 8001)
docker-compose up --build

# In a new terminal, run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Setup payment providers (optional)
docker-compose exec web python manage.py setup_payment_providers --provider chapa
```

### 3. Access the Application

- **🌐 API Base**: http://localhost:8001/api/v1/
- **👤 Admin Panel**: http://localhost:8001/admin/
- **📖 API Docs**: http://localhost:8001/api/docs/
- **📚 ReDoc**: http://localhost:8001/api/redoc/

## 📁 Project Structure

```
bazary/
├── 📁 apps/                    # Django applications
│   ├── authentication/        # Extended user system & JWT
│   ├── products/              # Products with variants system
│   ├── categories/            # Hierarchical categories
│   ├── payments/              # Cart, payments, transactions
│   └── core/                  # Shared utilities & models
├── 📁 bazary/                 # Main Django project
│   └── settings/              # Environment configurations
├── 📁 docs/                   # Comprehensive documentation
│   ├── database-schema.md     # Database structure
│   ├── payment-integration-completion.md  # Payment features
│   └── cart-to-payment-guide.md  # Complete workflow guide
├── 📁 .github/workflows/      # CI/CD pipelines
├──  docker-compose.yml      # Development setup
├── 🐳 Dockerfile             # Multi-stage build
└── 📋 README.md              # This file
```

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | Django + DRF | 5.0.14 |
| **Database** | PostgreSQL | 15+ |
| **Cache** | Redis | 7+ |
| **Authentication** | JWT (SimpleJWT) | Latest |
| **Payments** | Chapa, Stripe, PayPal | Latest |
| **Documentation** | Swagger/OpenAPI | 3.0 |
| **Testing** | Pytest + Factory Boy | Latest |
| **Containerization** | Docker + Compose | Latest |
| **CI/CD** | GitHub Actions | Latest |
| **Code Quality** | Black, Flake8, isort | Latest |

## 📊 Database Architecture

Bazary uses a robust PostgreSQL database design optimized for e-commerce operations. The schema supports complex product relationships, user management, shopping cart persistence, and multi-gateway payment processing.

### Entity Relationship Diagram

![Bazary Database ERD](./docs/database/Bazary%20ERD.png)

### Core Database Features

🏗️ **Normalized Design**
- **User Management**: Extended user profiles with addresses and verification
- **Product Catalog**: Products with variants, categories, tags, and images
- **Shopping Cart**: Persistent carts with real-time calculations
- **Payment System**: Multi-provider transactions with webhook support

📈 **Performance Optimizations**
- **Strategic Indexing**: Composite indexes for filtering and search operations
- **Query Optimization**: `select_related` and `prefetch_related` for N+1 prevention
- **Database Constraints**: Data integrity with foreign keys and check constraints
- **Connection Pooling**: Efficient database connection management

🔗 **Key Relationships**
- **One-to-Many**: User → Products, Categories → Products, Cart → CartItems
- **Many-to-Many**: Products ↔ Tags, ProductVariants ↔ VariantOptions
- **Hierarchical**: Categories with parent-child relationships
- **Transaction Flow**: Cart → Transaction → PaymentMethod → PaymentProvider

📚 **Detailed Documentation**
- **[Complete Schema](./docs/database/schema.md)** - Full data models and field definitions
- **[Relationships](./docs/database/relationships.md)** - Detailed relationship mappings
- **[Data Dictionary](./docs/database/data_dictionary.md)** - Field-by-field documentation
- **[DBML Schema](./docs/database/bazary_schema.dbml)** - Machine-readable schema definition

## 🌐 API Overview

### 🔐 Authentication Endpoints
- **Registration**: `POST /api/v1/auth/register/`
- **Login**: `POST /api/v1/auth/login/`
- **Token Refresh**: `POST /api/v1/auth/token/refresh/`
- **Password Reset**: `POST /api/v1/auth/password/reset/`
- **Profile Management**: `/api/v1/auth/profile/`
- **Address Management**: `/api/v1/auth/addresses/`

### 🛍️ Product Management
- **Products**: `/api/v1/products/`
  - List, create, update, delete products
  - Advanced filtering (category, price, availability)
  - Search with multiple criteria
- **Product Variants**: `/api/v1/products/{id}/variants/`
  - Size, color, material options
  - Individual pricing and stock levels
  - Variant-specific attributes
- **Categories**: `/api/v1/categories/`
  - Hierarchical category structure
  - Product associations and filtering
  - Category-specific attributes

### 🛒 Shopping Cart & Payments
- **Cart Management**: `/api/v1/payments/carts/`
  - `GET /carts/` - List user carts
  - `POST /carts/` - Create new cart
  - `GET /carts/current/` - Get/create current cart
  - `POST /carts/{id}/add_item/` - Add item to cart
  - `POST /carts/{id}/clear/` - Clear cart
  - `GET /carts/{id}/summary/` - Get cart summary

- **Cart Items**: `/api/v1/payments/cart-items/`
  - Item-level CRUD operations
  - Quantity updates and validation
  - Real-time price calculations

- **Transactions**: `/api/v1/payments/transactions/`
  - `POST /initialize/` - Start payment process
  - `POST /verify/` - Verify payment status
  - `GET /history/` - Payment history
  - `POST /refund/` - Process refunds

- **Payment Methods**: `/api/v1/payments/methods/`
  - Manage user payment methods
  - Secure payment information storage
  - Multi-provider support

### 📊 Example API Response

```json
{
  "count": 150,
  "next": "http://localhost:8001/api/v1/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Premium Wireless Headphones",
      "description": "High-quality wireless headphones with noise cancellation",
      "base_price": "299.99",
      "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics"
      },
      "variants": [
        {
          "id": 1,
          "size": "Standard",
          "color": "Black",
          "material": "Plastic",
          "price": "299.99",
          "stock_quantity": 50,
          "sku": "WH-001-BLK"
        }
      ],
      "images": [
        {
          "id": 1,
          "image": "/media/products/headphones-main.jpg",
          "alt_text": "Black wireless headphones",
          "is_primary": true
        }
      ],
      "tags": ["wireless", "audio", "premium"],
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## 📖 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[📊 Database Schema](./docs/database-schema.md)** - Complete data models and relationships
- **[� Payment Integration](./docs/payment-integration-completion.md)** - Payment system documentation
- **[🛒 Cart to Payment Guide](./docs/cart-to-payment-guide.md)** - Complete workflow examples
- **[🗺️ Feature Roadmap](./docs/v1-feature-roadmap.md)** - Development roadmap and progress
- **[🚀 Deployment Guide](./docs/deployment-guide.md)** - Production deployment instructions
- **[💻 Development Guide](./docs/development-guide.md)** - Local setup and coding standards

## 🏃‍♂️ Development Workflow

### Git Flow Process

```bash
# Start new feature
git flow feature start user-authentication

# Work on feature...
git add .
git commit -m "feat(auth): implement JWT authentication"

# Finish feature
git flow feature finish user-authentication
```

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run quality checks
black .           # Format code
flake8 .          # Lint code
isort .           # Sort imports
pytest            # Run tests
pytest --cov     # Check coverage
```

### Docker Development

```bash
# Start development environment
docker-compose up --build

# Run commands in container
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test

# View logs
docker-compose logs -f web
```

## 🚀 Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy to staging
railway up --service staging

# Deploy to production
railway up --service production
```

### Other Platforms

The application supports deployment to:
- **Railway** (Recommended)
- **Render**
- **DigitalOcean App Platform**
- **Custom VPS with Docker**

See the [Deployment Guide](./docs/deployment-guide.md) for detailed instructions.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest apps/products/tests/test_models.py

# Run tests in parallel
pytest -n auto
```

## 📊 API Usage Examples

### Authentication Flow

```bash
# Register user
curl -X POST http://localhost:8001/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login
curl -X POST http://localhost:8001/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### Cart to Payment Workflow

```bash
# 1. Get or create cart
curl -X GET http://localhost:8001/api/v1/payments/carts/current/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Add item to cart
curl -X POST http://localhost:8001/api/v1/payments/carts/{cart_id}/add_item/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "variant": 1,
    "quantity": 2
  }'

# 3. Initialize payment
curl -X POST http://localhost:8001/api/v1/payments/transactions/initialize/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cart": 1,
    "amount": "199.98",
    "currency": "ETB",
    "provider": "chapa"
  }'
```

### Product Management

```bash
# List products with variants
curl "http://localhost:8001/api/v1/products/?include_variants=true"

# Filter products by category and price
curl "http://localhost:8001/api/v1/products/?category=electronics&price_min=50&price_max=500"

# Search products
curl "http://localhost:8001/api/v1/products/?search=wireless+headphones"
```

## 🗺️ Roadmap & Current Status

### ✅ Phase 1: Core MVP (COMPLETED)
- [x] Project setup and documentation ✅
- [x] Docker development environment ✅
- [x] CI/CD pipeline configuration ✅
- [x] Extended user authentication system ✅
- [x] Advanced product management with variants ✅
- [x] Hierarchical category system ✅
- [x] Comprehensive API documentation ✅

### ✅ Phase 2: Advanced E-Commerce (COMPLETED)
- [x] Shopping cart functionality with persistence ✅
- [x] Payment integration (Chapa, Stripe, PayPal ready) ✅
- [x] Transaction management and verification ✅
- [x] Product variants system (size, color, material) ✅
- [x] Advanced filtering and search ✅
- [x] Image upload and management ✅
- [x] Stock management and validation ✅

### 🚧 Phase 3: Order Management (IN PROGRESS)
- [ ] Order creation and management system
- [ ] Order status tracking and updates
- [ ] Email notifications for orders
- [ ] Invoice generation and management
- [ ] Shipping integration

### 🔮 Phase 4: Hybrid Commerce (PLANNED)
- [ ] Service booking system
- [ ] Appointment scheduling
- [ ] Multi-vendor marketplace
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] Customer reviews and ratings

## 💳 Payment Integration Status

### ✅ Implemented Features
- **Multiple Payment Gateways**: Chapa (Ethiopian), Stripe, PayPal support
- **Transaction Management**: Complete payment lifecycle tracking
- **Webhook Support**: Real-time payment status updates
- **Refund System**: Full and partial refund processing
- **Security**: PCI DSS ready with secure token handling
- **Cart Integration**: Seamless cart-to-payment workflow

### 🎯 Supported Payment Methods
- **Chapa**: Ethiopian Birr (ETB) - Primary for local market
- **Stripe**: International payments with multiple currencies
- **PayPal**: Global payment processing
- **Bank Transfer**: Direct bank payment support

See the [Payment Integration Guide](./docs/payment-integration-completion.md) for detailed implementation.

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** our coding standards and write tests
4. **Commit** using conventional commit messages
5. **Push** to your branch and create a Pull Request

### Commit Convention

```bash
feat(scope): add new feature
fix(scope): bug fix
docs(scope): documentation update
style(scope): formatting changes
refactor(scope): code refactoring
test(scope): add tests
chore(scope): maintenance tasks
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Django** and **Django REST Framework** communities
- **Railway** for excellent hosting platform
- **GitHub Actions** for CI/CD infrastructure
- All the amazing open-source contributors

## 📞 Support & Contact

- **📋 Issues**: [GitHub Issues](https://github.com/legennd48/bazary/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/legennd48/bazary/discussions)
- **📧 Email**: [Contact](mailto:your-email@domain.com)
- **📖 Wiki**: [Project Wiki](https://github.com/legennd48/bazary/wiki)

---

**⭐ Star this repository if you find it helpful!**

Built with ❤️ by [legennd48](https://github.com/legennd48) and contributors.
