# Async Email Implementation Plan and Progress

This document tracks the implementation to move email sending off the request path, so users don’t wait on SMTP.

## Scope
- Registration verification emails
- Resend verification endpoint
- Password reset request emails
- Admin bulk “send_verification” action

## Design
- Use Celery with Redis broker/result backend.
- Add tasks in `apps/authentication/tasks.py`:
  - `send_verification_email_task(user_id, token_id)`
  - `send_password_reset_email_task(user_id, token_id)`
- Generate tokens in request, then enqueue on `transaction.on_commit`.
- Keep view responses immediate (200/201), while the worker sends emails and retries on transient failures.

## Infra
- Celery app in `bazary/celery.py`, imported in `bazary/__init__.py`.
- Settings in `bazary/settings/base.py` for `CELERY_*` (override via env):
  - `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_TASK_ALWAYS_EAGER`, time limits.
- Redis service provided via `docker-compose.yml`.
- Celery worker service (`worker`) already defined in `docker-compose.yml`.
- Local helpers: `make celery-worker`, `make celery-beat` (optional), `make celery-logs`.

## Implemented Changes
- Celery app and base settings added.
- `apps/authentication/tasks.py`: email tasks with retries, exponential backoff, structured logging (start/success).
- Registration flow enqueues verification email via `transaction.on_commit`.
- Resend verification endpoint enqueues task.
- Password reset request enqueues task.
- Admin bulk “send_verification” enqueues task.
- Docker Compose now includes `worker` service (Celery worker).
- Makefile targets for running/observing worker (`celery-worker`, `celery-beat`, `celery-logs`).

## Next Steps
- Add optional Celery Beat scheduler (if periodic tasks become needed).
- Introduce structured JSON logging or OpenTelemetry spans for tasks.
- Capture task failures with Sentry (if not already integrated).
- Switch to email provider SDK (e.g., SendGrid, Mailgun) for higher throughput and delivery analytics.
- Add metrics (queued count, success/failure latency) via Prometheus or StatsD.
- Consider bulk task batching if future high-volume email scenarios emerge.

## Validation
- In development, set `CELERY_TASK_ALWAYS_EAGER=true` to execute tasks inline while verifying code paths.
- In Docker, run worker alongside web using the same env.

## Rollback
- If needed, we can temporarily set `CELERY_TASK_ALWAYS_EAGER=true` to preserve behavior without a running worker.

---

## Performance Notes
- Registration endpoint no longer waits on SMTP; latency now dominated by DB inserts and token creation.
- Tasks are idempotent (retries safe). Token lookup is O(1) by PK.
- To further reduce endpoint latency, defer any non-essential profile initialization to a background job if added later.

Last updated: 2025-09-16