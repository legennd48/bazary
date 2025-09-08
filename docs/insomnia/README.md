# Insomnia – Bazary API Testing Guide

This guide shows two easy ways to test the entire Bazary API using Insomnia.

Recommended flow: import the live OpenAPI schema URL so Insomnia generates all requests automatically and stays up to date. As an alternative, you can import the provided Insomnia collection JSON in this folder.

## 1) Start the API locally

Make sure the API is running at http://localhost:8001.

Option A – with Docker (recommended):

```bash
docker-compose up -d
```

Option B – without Docker (SQLite dev):

```bash
make install
make runserver
```

Quick checks:

- Health: http://localhost:8001/health/
- Swagger UI (drf-yasg): http://localhost:8001/swagger/
- Spectacular schema JSON: http://localhost:8001/api/schema/

## 2) Recommended: Import by OpenAPI URL (auto-generated)

1. Open Insomnia → Create or select a Workspace.
2. Click “Create” → “From URL”.
3. Use one of these schema endpoints:
	- Spectacular (OpenAPI 3): http://localhost:8001/api/schema/
	- drf-yasg JSON: http://localhost:8001/swagger.json
4. Insomnia will generate folders/requests for all endpoints and tags.
5. Set an environment variable if needed (e.g., base URL). You can also set a default “Bearer Token” at the folder/workspace level once you login.

Tip: You can refresh the imported spec in Insomnia when the backend changes.

## 3) Alternative: Import the provided Insomnia collection

We’ve included a minimal collection that covers the common flows (health check, login, profile, products list) and wires Authorization from the login response automatically.

File: `docs/insomnia/bazary-insomnia.json`

Steps:

1. Open Insomnia → Application menu → “Import/Export” → “Import Data” → “From File”.
2. Select `bazary-insomnia.json`.
3. In the “Base Environment” set:
	- `base_url`: `http://localhost:8001`
	- `email`: your test user email
	- `password`: your test user password
4. Run the “Auth → Login (Token Pair)” request.
5. The “Authorization: Bearer …” header in other requests will automatically use the access token from the login response.

Note: If you don’t have a user yet, create one via Swagger UI or the OpenAPI-generated “Register” request, then login.

## 4) Using Git Sync with Insomnia

Insomnia can store your workspace (requests, environments) directly in Git so teams can share consistent API tests.

Two practical options:

- Keep Insomnia state at the repo root (Insomnia will create a `.insomnia/` folder) and commit it.
- Or point Git Sync to this repo’s `docs/insomnia/` directory to keep API testing assets scoped to docs.

How to set up:

1. In Insomnia, open your Workspace → “Setup Git Sync”.
2. Choose your local repository path (this project), and pick branch `develop`.
3. Optionally set the working directory to `docs/insomnia/`.
4. Commit and push from within Insomnia to share changes.

## 5) Auth tips in Insomnia

- Folder-level auth: Set “Bearer Token” at the workspace or folder level so all child requests inherit it.
- Dynamic token from login: In the Authorization header, select “Template Tag → Response → Body Attribute” and point it to the login request’s `access` field.
- Refresh tokens: Add a request for `/api/v1/auth/token/refresh/` and update the Bearer token when needed.

## 6) Useful endpoints

- Auth: `/api/v1/auth/token/`, `/api/v1/auth/profile/`, `/api/v1/auth/register/`
- Products: `/api/v1/products/products/`, `/api/v1/products/tags/`
- Categories: `/api/v1/categories/`
- Payments & Cart: `/api/v1/payments/…` (providers, methods, transactions, carts)

If you want, we can expand the collection to cover every endpoint and example payloads, but importing the live OpenAPI URL is the most maintainable way to keep Insomnia in sync.

