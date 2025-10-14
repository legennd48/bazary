# Celery Setup and Email Verification Guide

## 🚨 Important: Running Celery for Email Sending

**Email verification and password reset emails require Celery to be running!**

When you register a new user, the system queues an email task to Celery. If Celery isn't running, the email will never be sent.

---

## ✅ Quick Start - Development Mode

### Option 1: Run Everything Together (Recommended)

```bash
# This starts both Django server AND Celery worker
make dev
```

OR

```bash
./scripts/dev_server.sh
```

This will:
- ✅ Start Celery worker in the background
- ✅ Start Django development server
- ✅ Handle graceful shutdown (Ctrl+C stops both)

### Option 2: Manual Setup (Two Terminals)

**Terminal 1 - Django Server:**
```bash
cd /home/legennd/Software_repos/bazary
source bazary_env/bin/activate
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd /home/legennd/Software_repos/bazary
source bazary_env/bin/activate
celery -A bazary worker -l info
```

OR use the Makefile:
```bash
make celery-worker
```

### Option 3: Enable Eager Mode (Testing Only)

For quick testing without running a separate Celery worker:

**Edit `.env` file:**
```bash
CELERY_TASK_ALWAYS_EAGER=true
```

Then restart Django server.

⚠️ **Note**: This runs tasks synchronously (blocking). Slower but simpler for testing.

---

## 🔍 Check Celery Status

To verify Celery is running properly:

```bash
python manage.py check_celery
```

OR

```bash
make check-celery
```

This will show:
- ✅ Celery configuration
- ✅ Active workers
- ✅ Registered tasks
- ✅ Connection status

---

## 📧 Testing Email Verification

### 1. Start Both Services

```bash
make dev
```

### 2. Register a New User

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 3. Watch the Logs

In the Celery worker terminal, you should see:
```
[INFO] Task apps.authentication.tasks.send_verification_email_task received
[INFO] Task apps.authentication.tasks.send_verification_email_task succeeded
```

In Django logs:
```
INFO - Verification email sent to test@example.com
```

### 4. Check Your Email

Look for the verification email in the inbox of the registered email address.

---

## 🛠️ Troubleshooting

### "No Celery workers found"

**Solution**: Start a Celery worker
```bash
celery -A bazary worker -l info
```

### "Connection refused to Redis"

**Check if Redis is running:**
```bash
redis-cli ping
```

Should return: `PONG`

**If not running:**
```bash
# Ubuntu/Debian
sudo systemctl start redis

# Or install Redis
sudo apt install redis-server
```

### "User matching query does not exist" error

This happens when:
1. A user was deleted but their email task was still queued
2. The task is trying to send email to a non-existent user

**Solution**: 
- The task will auto-retry and eventually fail (this is normal)
- Or clear the Redis queue: `redis-cli FLUSHALL` (⚠️ clears ALL data in Redis)

### Emails not being sent

**Check:**
1. ✅ Celery worker is running (`make check-celery`)
2. ✅ Email settings in `.env` are correct
3. ✅ Gmail App Password is valid (if using Gmail)
4. ✅ Check Celery logs for errors

---

## 🐳 Using Docker Compose (Production-like)

The easiest way to run everything together:

```bash
docker-compose up
```

This automatically starts:
- ✅ PostgreSQL database
- ✅ Redis broker
- ✅ Django web server
- ✅ Celery worker

All services communicate automatically!

---

## 📝 Quick Commands Reference

| Command | Description |
|---------|-------------|
| `make dev` | Start Django + Celery together |
| `make runserver` | Start Django only |
| `make celery-worker` | Start Celery worker only |
| `make check-celery` | Check Celery status |
| `docker-compose up` | Start all services with Docker |

---

## 🔐 Email Configuration

Your `.env` file should have:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=false  # Set to true for testing without worker
```

---

## 💡 Best Practices

### Development
- Use `make dev` to run both services together
- OR run two separate terminals (one for Django, one for Celery)
- Check Celery status before testing emails

### Production
- Use Docker Compose or systemd services
- Enable monitoring (Flower)
- Set `CELERY_TASK_ALWAYS_EAGER=false`
- Use proper process manager (supervisor, systemd, docker)

---

## 🎯 Summary

**The #1 reason emails don't send: Celery worker is not running!**

Always remember:
1. ✅ Start Celery worker: `make celery-worker` or `make dev`
2. ✅ Check status: `make check-celery`
3. ✅ Keep Celery running alongside Django server

That's it! 🚀