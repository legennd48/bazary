# 🛍️ Hybrid Commerce Backend MVP Documentation

## 📦 Version 1: E-Commerce Core MVP

### ✅ Purpose

Build the foundational backend of a hybrid-commerce platform, starting with core e-commerce functionalities: product listing, cart, checkout, order management, and user accounts. This version will lay the groundwork for adding service-booking capabilities and other hybrid features in future versions.

### 👥 Target Users

- End customers (buyers)
- Business owner/admin
- Delivery personnel (future version)

---

## 📐 System Architecture Overview

- **Backend Framework**: Django 5.x (DRF for APIs)
- **Database**: PostgreSQL
- **Containerization**: Docker + Docker Compose (for development and deployment)
- **Environment Configuration**: `django-environ` for `.env` management
- **CI/CD**: GitHub Actions + GitHub Environments
- **Deployment Targets**: Render or DigitalOcean (TBD)

---

## ⚙️ Git Workflow Strategy

We will use the **Git Flow** branching strategy:

- `main`: production-ready code
- `develop`: active development base branch
- `feature/*`: new features
- `hotfix/*`: emergency fixes
- `release/*`: release candidates before merging to `main`

> All commits to `main` and `develop` are made via PRs with required CI passing.

---

## 🐳 Dockerized Development

### Dev Environment

- `Dockerfile.dev` for development with volume mounts and live reload
- `docker-compose.yml` runs:
  - Django app
  - PostgreSQL
  - Redis (future use)

### Commands

```bash
docker-compose up --build
```

### .env

- Stored in `.env.dev` (not committed)
- Managed using `django-environ`

---

## 🚀 CI/CD with GitHub Actions

### Pipelines

- `build.yml`: build & test Docker image
- `test.yml`: linting, security scan, and unit/integration tests
- `deploy.yml`: deploy to staging or production with approval gates

### Key CI/CD Features

- Auto-run on pull request to `develop` and `main`
- Secrets managed via GitHub Environments
- Deployment triggers based on branch/tag

---

## 🧪 Testing Strategy

### Tools:

- `pytest`
- `pytest-django`
- `factory_boy`
- `coverage`

### Levels:

- Unit tests for business logic and model methods
- API tests with Django REST Framework test client
- Integration tests for cart and checkout

---

## 🔔 Notifications System

### Email Notifications

- New account creation (Welcome email)
- Order confirmation & updates
- Password reset

### In-App Notifications *(Future Upgrade)*

- For now, placeholders in DB structure

### Email Tools

- SMTP (Mailgun or Gmail SMTP for development)
- HTML + plain text email templates

---

## 📊 Database Schema (v1)

### Tables:

- `User`
- `Product`
- `Category`
- `Cart`
- `CartItem`
- `Order`
- `OrderItem`
- `Address`
- `Payment` (placeholder)
- `Notification` (future use)

> All models will be written using Django ORM with clear relationships and reusable managers.

---

## 🧰 Admin Features

- Add/edit/delete products
- Manage orders & update status
- View user data and basic analytics

---

## 🔐 Security Considerations

- Django built-in password hashing
- HTTPS enforced in production
- CORS restricted using `django-cors-headers`
- Rate limiting via `django-ratelimit` *(future)*
- CSRF protection enabled

---

## 📦 Packaging for Production

- `Dockerfile.prod` (multi-stage build)
- `docker-compose.prod.yml`
- Static files collected and served via WhiteNoise or Nginx

---

## 🌐 Deployment Roadmap

### Staging:

-

### Production:

-

---

## 🧭 Future Roadmap (v2+)

- Service booking system (hybrid commerce)
- Availability calendar + scheduling
- Admin dashboard with revenue reports
- Delivery agent integration
- Mobile version
- In-app notification system

---

## 📛 Suggested Project Name

**Project Name**: `SilkCart`

> A soft-sounding, elegant brandable name that works for both products and services.

Alternate suggestions:

- `GlamCart`
- `Veloxa`
- `Heirloom`
- `GlowCommerce`

---

Let me know if you'd like Swagger/OpenAPI docs, ER diagrams, or frontend integration guidance added next.

