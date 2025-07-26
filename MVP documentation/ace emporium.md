# 🛒 E-Commerce Backend MVP Documentation

## 📘 Project Overview

This project is a robust and scalable backend system for an **e-commerce platform** designed to handle product catalog management, user authentication, and product discovery features (filtering, sorting, pagination). It aims to simulate a real-world, production-grade backend with a strong focus on scalability, security, and extensibility.

The MVP (Minimum Viable Product) includes:

- RESTful API for product and category management
- JWT-based authentication for secure access
- Swagger API documentation for frontend integration
- Database optimization for high performance
- Containerized deployment-ready architecture

> 🧠 Future versions will extend the platform into a hybrid-commerce system, adding service booking and appointment scheduling features.

---

## 🎯 MVP Goals

- Enable authenticated users to manage and view products
- Allow anonymous users to browse product listings
- Support API clients (mobile, web) with clear, documented endpoints
- Handle large product datasets efficiently with pagination and indexing
- Ensure clean, maintainable, and testable code with CI/CD readiness

---

## 🧱 Tech Stack

| Layer            | Technology                    |
| ---------------- | ----------------------------- |
| Framework        | Django, DRF                   |
| Database         | PostgreSQL                    |
| Auth             | JWT (SimpleJWT)               |
| Docs             | Swagger (drf-yasg)            |
| Testing          | Pytest, Factory Boy           |
| Caching          | Redis (planned)               |
| Containerization | Docker, Docker Compose        |
| Deployment       | Railway/Render (Docker-based) |
| Notifications    | Email (SMTP), In-app (future) |
| Version Control  | Git, GitHub                   |

---

## 📊 Database Schema (Simplified)

```text
User
├── id (UUID)
├── email (unique)
├── password (hashed)
├── is_admin (bool)
└── created_at

Category
├── id
├── name
└── created_at

Product
├── id
├── name
├── description
├── price
├── category (FK → Category)
├── in_stock (bool)
├── created_at
└── updated_at
```

> Additional fields like tags, image URLs, and discount price may be added in future phases.

---

## 🔐 Authentication & Authorization

- **JWT** for secure login and access control
- **User roles**: Admin (create/update/delete), Customer (read-only access)
- Token blacklisting for logout support
- Middleware for permission control

---

## 🔍 Product Discovery APIs

- Filtering by category, price range
- Sorting by price, date created
- Pagination via `?page=1&size=10`
- Rate limiting and throttling (for API protection)

---

## 📦 Product Management Features

- Admins can:
  - Create, update, delete product listings
  - Assign products to categories
  - Set stock availability and pricing
- Customers and anonymous users can:
  - Browse all available products
  - View product details by ID
- Products have searchable name and description fields (via `?search=`)

---

## 🧰 Admin Panel (Built-In)

- Django admin is preconfigured for managing:
  - Users
  - Products
  - Categories
- Admin-only endpoints for advanced operations (optional DRF ViewSets)

---

## 📫 Notifications

### ✅ Email Notifications (Planned for Production)

- **Welcome email** after user registration
- **Password reset link** with expiry token
- **Admin alerts** on product creation/deletion
- Email integration via SMTP or Mailgun

### 🛎️ In-App Notifications (Planned V2)

- Admin dashboard alerts for new user registrations or booking requests
- Notification table (user\_id, message, seen flag)

### 🔁 Reminder System (Planned V2)

- Daily/weekly digests
- Upcoming appointment reminders (for service booking)

---

## 🧪 Testing Strategy

- **Pytest + Factory Boy** for unit and integration tests
- Test coverage > 85%
- CI setup for auto-testing on pull requests
- Types of tests:
  - Model tests
  - Serializer validation tests
  - API endpoint tests (CRUD, auth, filtering)
  - Permission tests (admin vs user)

---

## 🐳 Containerization Plan

### Files

- `Dockerfile` – for building the app
- `docker-compose.yml` – defines Django, Postgres, Redis services
- `.env` file – for managing environment secrets

### Services

- Django app (Gunicorn)
- PostgreSQL DB
- Redis (future caching)
- Swagger UI available via `/swagger/`

---

## 🚀 Deployment Plan

- Platform: Railway.app, Render.com, or Docker-compatible VPS
- CI/CD pipeline with GitHub Actions:
  - Lint → Test → Build → Deploy
- Docker container push to GitHub Packages
- Auto-deploy on `main` branch push (optional)

---

## 🔁 Version Control & Git Strategy

- GitHub repository with the following branching model:
  - `main`: production-ready code
  - `dev`: integration of features
  - `feature/xyz`: individual features or fixes

### Commit Guidelines

```bash
feat: add product model
fix: correct JWT expiry bug
docs: update Swagger docs
perf: add index to product table
test: add product view tests
```

---

## 📄 API Documentation

- Auto-generated using **drf-yasg**
- Swagger UI at `/swagger/`
- Redoc (optional)
- Includes:
  - Endpoint list
  - Parameters and schema
  - Example responses
  - Error messages and status codes

---

## 🧠 Future-Proofing (V2+ Roadmap)

| Feature                     | Description                               |
| --------------------------- | ----------------------------------------- |
| Service Booking             | Allow users to schedule salon sessions    |
| Admin Dashboard             | Manage services, users, and bookings      |
| Ratings & Reviews           | Add feedback system for products/services |
| Payment Gateway Integration | Stripe/Flutterwave integration            |
| Role-Based Permissions      | Granular access control                   |
| Mobile App Integration      | Add CORS and token refresh for mobile     |

---

## 🧾 Appendix

### Requirements (initial)

```text
Django==4.x
djangorestframework
psycopg2-binary
drf-yasg
django-filter
djangorestframework-simplejwt
pytest-django
```

### Tools Used

- GitHub Projects (task tracking)
- Postman for API testing
- Swagger UI for frontend integration
- Docker Desktop or Podman

---

## 📌 Final Notes

This documentation outlines the design and implementation of a **production-worthy MVP** for an e-commerce backend. It balances current delivery goals with long-term extensibility, enabling seamless integration of hybrid-commerce features in the near future.

> 👨‍💻 Maintainer: Backend Engineer (7+ years Django experience) 📅 Last Updated: July 25, 2025

