# 🗺️ Bazary V1.0 Feature Roadmap

**### 1. 🗄️ **Database Seeding & Documentation** ✅ COMPLETEDast Updated:** August 3, 2025  
**Current Status:** Post-Database Seeding & Documentation Implementation  
**Target:** Production-Ready V1.0 Release  

---

## 🎯 Executive Summary

Based on the comprehensive V1.0 assessment, Bazary has successfully completed its **core MVP requirements**, **API Security & Permissions**, and **Database Seeding & Documentation** with excellent code quality and comprehensive documentation. The next phase focuses on CI/CD automation followed by enhanced user and product management features to ensure enterprise-grade reliability and scalability.

**Current Branch:** `feature/database-seeding-documentation`  
**Completed Features:** ✅ Swagger Documentation, ✅ API Security & Permissions, ✅ Database Seeding & Documentation  
**Next Phase:** User Management Enhancement & Product Management  

---

## 📊 Feature Completion Status

| Category | Status | Priority | Estimated Effort |
|----------|--------|----------|------------------|
| 🏗️ **Core MVP** | ✅ Complete | Critical | 0 days |
| 📚 **API Documentation** | ✅ Complete | High | 0 days |
| 🔒 **Security & Permissions** | ✅ Complete | Critical | 0 days |
| 🗄️ **Database Seeding & Documentation** | ✅ Complete | Critical | 0 days |
| 🚀 **CI/CD Pipeline Setup** | ✅ Complete | High | 0 days |
| 👥 **User Management** | 🟡 Needs Enhancement | High | 2-3 days |
| 🛍️ **Product Management** | 🟡 Needs Enhancement | High | 2-4 days |
| ⚡ **Performance & Caching** | 🔴 Missing | Medium | 2-3 days |
| 📧 **Notifications** | 🔴 Missing | Medium | 1-2 days |
| 🧪 **Testing Enhancements** | 🟡 Needs Improvement | Medium | 1-2 days |

---

## 🚀 Remaining Features for V1.0

### 1. �️ **Database Seeding & Documentation**
**Git Flow Branch:** `feature/database-seeding-documentation`  
**Priority:** Critical  
**Status:** ✅ **COMPLETED ON AUGUST 3, 2025**  

#### ✅ Completed Implementation
✅ **Database Seeding System**
- ✅ Created Django management command for database seeding (`seed_database.py`)
- ✅ Implemented realistic test data generators with 10 users, 24 categories, 10 tags, 25 products
- ✅ Added user accounts with different roles (Admin, Staff, Customer) with proper permissions
- ✅ Created sample products with realistic pricing, descriptions, and categorization
- ✅ Generated hierarchical categories (Electronics, Clothing, Books, Home & Garden, Sports)
- ✅ Added comprehensive tag system with color coding
- ✅ Implemented data relationship integrity with proper foreign keys

✅ **Database Schema Documentation**
- ✅ Complete schema documentation (`docs/database/schema.md`)
- ✅ Detailed relationship mapping (`docs/database/relationships.md`)
- ✅ Comprehensive data dictionary (`docs/database/data_dictionary.md`)
- ✅ Performance optimization guidelines and index strategies
- ✅ Database maintenance and scaling considerations

✅ **Database Visualization**
- ✅ Created DBML file for dbdiagram.io (`docs/database/bazary_schema.dbml`)
- ✅ Visual database diagram with all tables, relationships, and constraints
- ✅ Comprehensive README for database documentation (`docs/database/README.md`)

#### 📊 Results Achieved
- ✅ Database seeding completes in 2.33 seconds with realistic data
- ✅ All API endpoints have meaningful test data for development and testing
- ✅ Complete database documentation with visual diagrams available
- ✅ Developer setup requires single `python manage.py seed_database` command
- ✅ Comprehensive seeding options: `--reset`, `--verbose`, `--users=N`, `--products=N`

---

### 2. 🚀 **CI/CD Pipeline Setup & Validation** ✅ COMPLETED
**Git Flow Branch:** `feature/cicd-pipeline-setup`  
**Priority:** High  
**Status:** ✅ **COMPLETED ON AUGUST 3, 2025**  

#### ✅ Completed Implementation
✅ **GitHub Actions CI/CD Workflow**
- ✅ Created comprehensive CI/CD pipeline (`.github/workflows/ci.yml`)
- ✅ Implemented code quality checks (bandit, flake8, isort, black)
- ✅ Added testing matrix (unit, integration, API tests)
- ✅ Integrated API documentation validation
- ✅ Set up Docker build and push to Docker Hub
- ✅ Configured automated deployment to development and production environments
- ✅ Added post-deployment monitoring and health checks

✅ **EC2 Server Setup & Deployment**
- ✅ Created comprehensive EC2 setup script (`scripts/setup-ec2-server.sh`)
- ✅ Automated Docker and Docker Compose installation
- ✅ Configured Nginx reverse proxy with SSL support
- ✅ Set up Let's Encrypt SSL certificate automation
- ✅ Implemented firewall configuration with UFW
- ✅ Created project directory structure for multi-environment deployment
- ✅ Added automated deployment scripts for production and development

✅ **Production Configuration**
- ✅ Created production Docker compose configuration (`docker-compose.prod.yml`)
- ✅ Implemented health checks for all services (PostgreSQL, Redis, Django, Nginx)
- ✅ Set up proper networking and volume management
- ✅ Created environment templates for secure configuration
- ✅ Added database backup automation before deployments

✅ **Documentation & Security**
- ✅ Created comprehensive setup guide (`docs/cicd-setup-guide.md`)
- ✅ Documented GitHub secrets configuration
- ✅ Added step-by-step deployment procedures
- ✅ Created troubleshooting guide for common issues
- ✅ Updated `.gitignore` to protect environment files

---

### 3. 👥 **User Management Enhancement** 🔄 NEXT PRIORITY
**Git Flow Branch:** `feature/user-management-enhancement`  
**Priority:** High  
**Estimated Effort:** 2-3 days  

#### 🎯 Scope & Objectives
- Enhance user profile management and administration
- Implement advanced user authentication features
- Add user activity tracking and audit logging
- Create comprehensive user management dashboard
- Establish user role and permission refinements

#### 📋 Detailed Tasks

##### **GitHub Actions Workflow Setup**
- [ ] Create main CI/CD workflow configuration
- [ ] Set up matrix testing for multiple Python versions
- [ ] Configure environment-specific variables
- [ ] Add workflow triggers for different branches
- [ ] Implement parallel job execution for speed

##### **Automated Testing Pipeline**
- [ ] Configure automated unit test execution
- [ ] Add integration test automation
- [ ] Implement database migration testing
- [ ] Set up API endpoint testing with seed data
- [ ] Add test coverage reporting and requirements

##### **Code Quality & Security**
- [ ] Integrate linting and code formatting checks
- [ ] Add security vulnerability scanning
- [ ] Implement dependency checking and updates
- [ ] Set up code quality metrics and reporting
- [ ] Add pre-commit hooks for development

##### **Deployment Automation**
- [ ] Configure staging environment deployment
- [ ] Set up production deployment workflow
- [ ] Add database migration automation
- [ ] Implement rollback capabilities
- [ ] Create deployment status monitoring

##### **Documentation & Monitoring**
- [ ] Automate Swagger documentation updates
- [ ] Set up build status reporting
- [ ] Add performance regression testing
- [ ] Implement deployment notifications
- [ ] Create CI/CD dashboard and monitoring

#### 🔧 Technical Implementation
```yaml
# Example Structure
.github/workflows/
├── ci.yml              # Main CI pipeline
├── deploy-staging.yml  # Staging deployment
├── deploy-prod.yml     # Production deployment
└── security-scan.yml   # Security scanning

scripts/
├── setup-env.sh       # Environment setup
├── run-tests.sh       # Test execution
└── deploy.sh          # Deployment script
```

#### 📊 Success Criteria
- All tests pass automatically on every commit
- Code quality gates prevent poor code from merging
- Security vulnerabilities detected automatically
- Staging deployment works seamlessly
- Production deployment process is bulletproof

---

### 3. 👥 **User Management System Enhancement**
**Git Flow Branch:** `feature/user-management-system`  
**Priority:** High  
**Estimated Effort:** 2-3 days  

#### 🎯 Scope & Objectives
- Enhance user profile management
- Add admin user management endpoints
- Implement user role assignment
- Add account verification system
- Create password reset functionality

#### 📋 Detailed Tasks

##### **Enhanced User Profiles**
- [ ] Extend user profile with additional fields
- [ ] Add profile image upload functionality
- [ ] Implement profile update validation
- [ ] Create profile privacy settings
- [ ] Add user activity tracking

##### **Admin User Management**
- [ ] Create comprehensive admin user endpoints
- [ ] Add bulk user operations (activate/deactivate)
- [ ] Implement user role management
- [ ] Add user search and filtering
- [ ] Create user management Swagger documentation

##### **Account Verification System**
- [ ] Implement email verification for registration
- [ ] Add phone number verification (optional)
- [ ] Create verification token management
- [ ] Add resend verification functionality
- [ ] Implement account activation workflow

##### **Password Management**
- [ ] Create password reset via email
- [ ] Add password strength validation
- [ ] Implement password history tracking
- [ ] Add password change notifications
- [ ] Create secure password reset tokens

##### **User Role System**
- [ ] Define user roles (Admin, Staff, Customer)
- [ ] Implement role-based access control
- [ ] Add role assignment endpoints
- [ ] Create role permission matrices
- [ ] Add role-based UI rendering support

#### 🔧 Technical Implementation
```python
# Example Structure
apps/authentication/
├── models/
│   ├── user.py           # Enhanced user model
│   ├── profile.py        # User profile model
│   └── verification.py   # Verification tokens
├── views/
│   ├── admin.py          # Admin user management
│   ├── profile.py        # Profile management
│   └── verification.py   # Account verification
└── serializers/
    ├── admin.py          # Admin serializers
    ├── profile.py        # Profile serializers
    └── verification.py   # Verification serializers
```

#### 📊 Success Criteria
- Complete user profile management system
- Admin can manage all user accounts
- Email verification working
- Password reset functionality operational
- Role-based access control implemented

---

### 3. � **User Management System Enhancement**
**Git Flow Branch:** `feature/user-management-system`  
**Priority:** High  
**Estimated Effort:** 2-3 days  

#### 🎯 Scope & Objectives
- Enhance user profile management
- Add admin user management endpoints
- Implement user role assignment
- Add account verification system
- Create password reset functionality

#### 📋 Detailed Tasks

##### **Enhanced User Profiles**
- [ ] Extend user profile with additional fields
- [ ] Add profile image upload functionality
- [ ] Implement profile update validation
- [ ] Create profile privacy settings
- [ ] Add user activity tracking

##### **Admin User Management**
- [ ] Create comprehensive admin user endpoints
- [ ] Add bulk user operations (activate/deactivate)
- [ ] Implement user role management
- [ ] Add user search and filtering
- [ ] Create user management Swagger documentation

##### **Account Verification System**
- [ ] Implement email verification for registration
- [ ] Add phone number verification (optional)
- [ ] Create verification token management
- [ ] Add resend verification functionality
- [ ] Implement account activation workflow

##### **Password Management**
- [ ] Create password reset via email
- [ ] Add password strength validation
- [ ] Implement password history tracking
- [ ] Add password change notifications
- [ ] Create secure password reset tokens

##### **User Role System**
- [ ] Define user roles (Admin, Staff, Customer)
- [ ] Implement role-based access control
- [ ] Add role assignment endpoints
- [ ] Create role permission matrices
- [ ] Add role-based UI rendering support

#### 🔧 Technical Implementation
```python
# Example Structure
apps/authentication/
├── models/
│   ├── user.py           # Enhanced user model
│   ├── profile.py        # User profile model
│   └── verification.py   # Verification tokens
├── views/
│   ├── admin.py          # Admin user management
│   ├── profile.py        # Profile management
│   └── verification.py   # Account verification
└── serializers/
    ├── admin.py          # Admin serializers
    ├── profile.py        # Profile serializers
    └── verification.py   # Verification serializers
```

#### 📊 Success Criteria
- Complete user profile management system
- Admin can manage all user accounts
- Email verification working
- Password reset functionality operational
- Role-based access control implemented

---

### 4. �🛍️ **Enhanced Product Management**
**Git Flow Branch:** `feature/enhanced-product-management`  
**Priority:** High  
**Estimated Effort:** 2-4 days  

#### 🎯 Scope & Objectives
- Add product image upload and management
- Implement product variants and options
- Add bulk product operations
- Enhance product search and analytics
- Create product review system foundation

#### 📋 Detailed Tasks

##### **Product Media Management**
- [ ] Implement multiple image upload for products
- [ ] Add image compression and optimization
- [ ] Create image ordering and primary image selection
- [ ] Add image validation and security
- [ ] Implement image CDN integration ready

##### **Product Variants & Options**
- [ ] Create product variant models (size, color, etc.)
- [ ] Implement variant-specific pricing
- [ ] Add variant stock management
- [ ] Create variant selection API endpoints
- [ ] Add variant-based filtering

##### **Bulk Operations & Management**
- [ ] Add bulk product import/export
- [ ] Implement bulk price updates
- [ ] Create bulk stock management
- [ ] Add bulk category assignment
- [ ] Implement bulk product activation/deactivation

##### **Enhanced Search & Analytics**
- [ ] Implement advanced search with ranking
- [ ] Add search suggestions and autocomplete
- [ ] Create product view tracking
- [ ] Add popular products analytics
- [ ] Implement search result optimization

##### **Product Quality & Validation**
- [ ] Add comprehensive product validation
- [ ] Implement duplicate detection
- [ ] Create product quality scoring
- [ ] Add automated product recommendations
- [ ] Implement product data integrity checks

#### 🔧 Technical Implementation
```python
# Example Structure
apps/products/
├── models/
│   ├── variants.py       # Product variants
│   ├── media.py          # Product images/media
│   └── analytics.py      # Product analytics
├── views/
│   ├── bulk.py           # Bulk operations
│   ├── media.py          # Media management
│   └── analytics.py      # Analytics endpoints
└── managers/
    ├── search.py         # Enhanced search
    └── recommendations.py # Product recommendations
```

#### 📊 Success Criteria
- Product images upload and management working
- Product variants system operational
- Bulk operations available for admins
- Enhanced search delivering relevant results
- Analytics tracking product performance

---

### 4. 🛍️ **Enhanced Product Management**
**Git Flow Branch:** `feature/enhanced-product-management`  
**Priority:** High  
**Estimated Effort:** 2-4 days  

#### 🎯 Scope & Objectives
- Add product image upload and management
- Implement product variants and options
- Add bulk product operations
- Enhance product search and analytics
- Create product review system foundation

#### 📋 Detailed Tasks

##### **Product Media Management**
- [ ] Implement multiple image upload for products
- [ ] Add image compression and optimization
- [ ] Create image ordering and primary image selection
- [ ] Add image validation and security
- [ ] Implement image CDN integration ready

##### **Product Variants & Options**
- [ ] Create product variant models (size, color, etc.)
- [ ] Implement variant-specific pricing
- [ ] Add variant stock management
- [ ] Create variant selection API endpoints
- [ ] Add variant-based filtering

##### **Bulk Operations & Management**
- [ ] Add bulk product import/export
- [ ] Implement bulk price updates
- [ ] Create bulk stock management
- [ ] Add bulk category assignment
- [ ] Implement bulk product activation/deactivation

##### **Enhanced Search & Analytics**
- [ ] Implement advanced search with ranking
- [ ] Add search suggestions and autocomplete
- [ ] Create product view tracking
- [ ] Add popular products analytics
- [ ] Implement search result optimization

##### **Product Quality & Validation**
- [ ] Add comprehensive product validation
- [ ] Implement duplicate detection
- [ ] Create product quality scoring
- [ ] Add automated product recommendations
- [ ] Implement product data integrity checks

#### 🔧 Technical Implementation
```python
# Example Structure
apps/products/
├── models/
│   ├── variants.py       # Product variants
│   ├── media.py          # Product images/media
│   └── analytics.py      # Product analytics
├── views/
│   ├── bulk.py           # Bulk operations
│   ├── media.py          # Media management
│   └── analytics.py      # Analytics endpoints
└── managers/
    ├── search.py         # Enhanced search
    └── recommendations.py # Product recommendations
```

#### 📊 Success Criteria
- Product images upload and management working
- Product variants system operational
- Bulk operations available for admins
- Enhanced search delivering relevant results
- Analytics tracking product performance

---

### 5. ⚡ **Performance & Caching Layer**
**Git Flow Branch:** `feature/performance-caching`  
**Priority:** Medium  
**Estimated Effort:** 2-3 days  

#### 🎯 Scope & Objectives
- Implement Redis caching layer
- Add database query optimization
- Create CDN-ready static file handling
- Implement API response caching
- Add performance monitoring

#### 📋 Detailed Tasks

##### **Redis Caching Implementation**
- [ ] Set up Redis configuration for all environments
- [ ] Implement model-level caching
- [ ] Add API response caching
- [ ] Create cache invalidation strategies
- [ ] Add cache monitoring and metrics

##### **Database Optimization**
- [ ] Optimize database queries with indexes
- [ ] Implement connection pooling
- [ ] Add database query monitoring
- [ ] Create database performance metrics
- [ ] Optimize N+1 query problems

##### **Static File & CDN Optimization**
- [ ] Configure static file compression
- [ ] Implement CDN-ready file structure
- [ ] Add image optimization pipeline
- [ ] Create static file versioning
- [ ] Implement lazy loading support

#### 📊 Success Criteria
- Redis caching operational
- Database queries optimized
- Static files CDN-ready
- Performance metrics available

---

### 5. ⚡ **Performance & Caching Layer**
**Git Flow Branch:** `feature/performance-caching`  
**Priority:** Medium  
**Estimated Effort:** 2-3 days  

#### 🎯 Scope & Objectives
- Implement Redis caching layer
- Add database query optimization
- Create CDN-ready static file handling
- Implement API response caching
- Add performance monitoring

#### 📋 Detailed Tasks

##### **Redis Caching Implementation**
- [ ] Set up Redis configuration for all environments
- [ ] Implement model-level caching
- [ ] Add API response caching
- [ ] Create cache invalidation strategies
- [ ] Add cache monitoring and metrics

##### **Database Optimization**
- [ ] Optimize database queries with indexes
- [ ] Implement connection pooling
- [ ] Add database query monitoring
- [ ] Create database performance metrics
- [ ] Optimize N+1 query problems

##### **Static File & CDN Optimization**
- [ ] Configure static file compression
- [ ] Implement CDN-ready file structure
- [ ] Add image optimization pipeline
- [ ] Create static file versioning
- [ ] Implement lazy loading support

#### 📊 Success Criteria
- Redis caching operational
- Database queries optimized
- Static files CDN-ready
- Performance metrics available

---

### 6. 📧 **Notification System**
**Git Flow Branch:** `feature/notification-system`  
**Priority:** Medium  
**Estimated Effort:** 1-2 days  

#### 🎯 Scope & Objectives
- Implement email notification system
- Add user registration emails
- Create password reset emails
- Add admin notification system
- Implement notification preferences

#### 📋 Detailed Tasks
- [ ] Configure SMTP email backend
- [ ] Create email templates for all notifications
- [ ] Implement email queue system
- [ ] Add notification preferences for users
- [ ] Create admin notification dashboard

---

### 6. 📧 **Notification System**
**Git Flow Branch:** `feature/notification-system`  
**Priority:** Medium  
**Estimated Effort:** 1-2 days  

#### 🎯 Scope & Objectives
- Implement email notification system
- Add user registration emails
- Create password reset emails
- Add admin notification system
- Implement notification preferences

#### 📋 Detailed Tasks
- [ ] Configure SMTP email backend
- [ ] Create email templates for all notifications
- [ ] Implement email queue system
- [ ] Add notification preferences for users
- [ ] Create admin notification dashboard

---

### 7. 🧪 **Testing & Quality Assurance Enhancement**
**Git Flow Branch:** `feature/testing-enhancement`  
**Priority:** Medium  
**Estimated Effort:** 1-2 days  

#### 🎯 Scope & Objectives
- Increase test coverage to 80%+
- Add integration tests
- Implement performance testing
- Add security testing
- Create automated testing pipeline

#### 📋 Detailed Tasks
- [ ] Add comprehensive unit tests for new features
- [ ] Implement API integration tests
- [ ] Add security penetration testing
- [ ] Create performance benchmarking tests
- [ ] Enhance CI/CD testing pipeline

---

### 7. 🧪 **Testing & Quality Assurance Enhancement**
**Git Flow Branch:** `feature/testing-enhancement`  
**Priority:** Medium  
**Estimated Effort:** 1-2 days  

#### 🎯 Scope & Objectives
- Increase test coverage to 80%+
- Add integration tests
- Implement performance testing
- Add security testing
- Create automated testing pipeline

#### 📋 Detailed Tasks
- [ ] Add comprehensive unit tests for new features
- [ ] Implement API integration tests
- [ ] Add security penetration testing
- [ ] Create performance benchmarking tests
- [ ] Enhance CI/CD testing pipeline

---

## 📅 Development Timeline

### **Phase 1: Foundation Infrastructure (Days 1-4)**
- Week 1: Database Seeding & Documentation (Days 1-2)
- Week 1: CI/CD Pipeline Setup & Validation (Days 3-4)
- Focus: Foundational infrastructure for rapid development

### **Phase 2: User Management (Days 5-7)**
- Week 2: User Management System Enhancement
- Focus: Complete user lifecycle management

### **Phase 3: Product Enhancement (Days 8-11)**
- Week 2-3: Enhanced Product Management
- Focus: Advanced product features and media

### **Phase 4: Performance & Quality (Days 12-15)**
- Week 3: Performance, Caching, and Testing
- Focus: Optimization and quality assurance

### **Phase 5: Final Polish (Days 16-17)**
- Week 3: Notification System and Final Testing
- Focus: Complete V1.0 feature set

---

## 🎯 V1.0 Success Criteria

### **Technical Requirements**
- [ ] All API endpoints secured with proper permissions
- [ ] Rate limiting implemented and tested
- [ ] User management system complete
- [ ] Product management enhanced with media support
- [ ] Test coverage ≥ 80%
- [ ] Performance optimized with caching
- [ ] Email notifications operational

### **Security Requirements**
- [ ] Authentication and authorization bulletproof
- [ ] Input validation comprehensive
- [ ] Security headers properly configured
- [ ] CORS optimized for production
- [ ] Rate limiting protecting against abuse

### **User Experience Requirements**
- [ ] Complete user profile management
- [ ] Email verification and password reset
- [ ] Admin user management interface
- [ ] Enhanced product browsing experience
- [ ] Fast and responsive API performance

### **Production Readiness**
- [ ] Environment-specific configurations
- [ ] Database optimization complete
- [ ] Static file handling optimized
- [ ] Error handling and logging comprehensive
- [ ] Monitoring and metrics available

---

## 🔄 Git Flow Strategy

### **Feature Development Process**
1. **Start Feature:** `git flow feature start feature-name`
2. **Development:** Work on feature branch
3. **Testing:** Comprehensive testing on feature branch
4. **Documentation:** Update docs and Swagger
5. **Code Review:** Self-review and validation
6. **Finish Feature:** `git flow feature finish feature-name`
7. **Integration Testing:** Test on develop branch

### **Branch Naming Convention**
- `feature/database-seeding-documentation`
- `feature/cicd-pipeline-setup`
- `feature/user-management-system`
- `feature/enhanced-product-management`
- `feature/performance-caching`
- `feature/notification-system`
- `feature/testing-enhancement`

---

## 📊 Resource Allocation

### **Development Effort Distribution**
- **Security & Permissions:** 30% (Critical path)
- **User Management:** 20% (High impact)
- **Product Enhancement:** 25% (High value)
- **Performance & Caching:** 15% (Optimization)
- **Testing & Quality:** 10% (Quality assurance)

### **Risk Mitigation**
- **Security Features:** Highest priority due to production requirements
- **User Management:** Essential for admin operations
- **Product Features:** Key differentiation for marketplace
- **Performance:** Important for user experience
- **Testing:** Ensures quality and reliability

---

## 🎉 Post-V1.0 Roadmap Preview

### **Version 1.1 Features**
- Shopping cart and checkout system
- Order management and tracking
- Payment gateway integration (Stripe/PayPal)
- Advanced analytics dashboard

### **Version 2.0 Features**
- Service booking system (hybrid commerce)
- Multi-vendor marketplace
- Mobile app API enhancements
- Advanced recommendation engine

---

## 🔗 Related Documentation

- [V1.0 Assessment Report](../V1_ASSESSMENT_REPORT.md)
- [Technical Architecture](./technical-architecture.md)
- [Development Guide](./development-guide.md)
- [Git Flow Guide](./git-flow-guide.md)
- [Deployment Guide](./deployment-guide.md)

---

**Next Action:** Start with critical security features using:
```bash
git flow feature start api-security-permissions
```

*This roadmap will be updated as features are completed and new requirements emerge.*
