# 📧 Email Service Setup Guide

**Last Updated:** August 6, 2025  
**Purpose:** Production-ready email configuration for Bazary  

---

## 🎯 Overview

This guide covers setting up professional email services for Bazary's user management features including email verification, password resets, and notifications.

---

## 📋 Email Service Options

### 1. **SendGrid** (Recommended)
- **Free Tier**: 100 emails/day
- **Paid Plans**: Starting at $19.95/month for 50,000 emails
- **Features**: High deliverability, detailed analytics, templates
- **Best For**: Production applications with high volume

### 2. **Mailgun**
- **Free Tier**: 5,000 emails/month for 3 months
- **Paid Plans**: $35/month for 50,000 emails
- **Features**: Powerful API, email validation, analytics
- **Best For**: Developer-friendly with advanced features

### 3. **Amazon SES**
- **Pricing**: $0.10 per 1,000 emails
- **Features**: High deliverability, AWS integration
- **Best For**: AWS-hosted applications

### 4. **Gmail SMTP** (Development Only)
- **Free**: Personal Gmail account
- **Limitations**: Daily send limits, not for production
- **Best For**: Development and testing

---

## 🚀 SendGrid Setup (Recommended)

### Step 1: Create SendGrid Account
1. Go to [SendGrid.com](https://sendgrid.com)
2. Sign up for a free account
3. Verify your email address
4. Complete account setup

### Step 2: Get API Key
1. Go to Settings → API Keys
2. Click "Create API Key"
3. Choose "Restricted Access"
4. Grant permissions:
   - Mail Send: FULL ACCESS
   - Template Engine: READ ACCESS (if using templates)
5. Copy the API key (save it securely)

### Step 3: Domain Authentication (Optional but Recommended)
1. Go to Settings → Sender Authentication
2. Click "Authenticate Your Domain"
3. Follow DNS setup instructions
4. Verify domain ownership

### Step 4: Configure Django Settings

```python
# In your settings/base.py or settings/production.py

# SendGrid SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # This is literal 'apikey'
EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY')  # Your actual API key
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')

# SendGrid API Configuration (Alternative to SMTP)
SENDGRID_API_KEY = config('SENDGRID_API_KEY')
```

### Step 5: Environment Variables
Add to your `.env` file:
```bash
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SITE_NAME=Bazary
FRONTEND_URL=https://yourdomain.com
```

---

## 🔧 Mailgun Setup (Alternative)

### Step 1: Create Mailgun Account
1. Go to [Mailgun.com](https://mailgun.com)
2. Sign up for a free account
3. Verify your phone number

### Step 2: Get Domain and API Key
1. Go to Domains → Add New Domain
2. Follow domain verification steps
3. Get SMTP credentials from domain settings
4. Copy API key from Settings

### Step 3: Configure Django Settings
```python
# Mailgun SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = config('MAILGUN_SMTP_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')

# Mailgun API Configuration
MAILGUN_API_KEY = config('MAILGUN_API_KEY')
MAILGUN_DOMAIN = config('MAILGUN_DOMAIN')
```

### Step 4: Environment Variables
```bash
# Mailgun Configuration
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=yourdomain.com
MAILGUN_SMTP_LOGIN=postmaster@yourdomain.com
MAILGUN_SMTP_PASSWORD=your_smtp_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

---

## 🧪 Gmail SMTP Setup (Development Only)

### Step 1: Enable App Passwords
1. Go to Google Account settings
2. Security → 2-Step Verification (enable if not already)
3. App passwords → Generate new password
4. Copy the 16-character password

### Step 2: Configure Django Settings
```python
# Gmail SMTP Configuration (DEVELOPMENT ONLY)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('GMAIL_EMAIL')
EMAIL_HOST_PASSWORD = config('GMAIL_APP_PASSWORD')
DEFAULT_FROM_EMAIL = config('GMAIL_EMAIL')
```

### Step 3: Environment Variables
```bash
# Gmail Configuration (Development Only)
GMAIL_EMAIL=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
DEFAULT_FROM_EMAIL=your.email@gmail.com
```

---

## 🔐 Security Best Practices

### 1. **Environment Variables**
```bash
# Never commit these to version control
# Use .env files and environment-specific configs

# Production
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=https://yourdomain.com

# Development
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@dev.yourdomain.com
FRONTEND_URL=http://localhost:3000
```

### 2. **Email Templates Security**
```python
# Secure email template handling
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_secure_email(user, template_name, context):
    context.update({
        'user': user,
        'site_name': settings.SITE_NAME,
        'frontend_url': settings.FRONTEND_URL,
    })
    
    html_message = render_to_string(f'emails/{template_name}.html', context)
    plain_message = strip_tags(html_message)
    
    # Validate recipient
    if not user.email or '@' not in user.email:
        raise ValueError("Invalid recipient email")
    
    send_mail(
        subject=context.get('subject', f'Notification from {settings.SITE_NAME}'),
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
```

### 3. **Rate Limiting**
```python
# Add rate limiting for email sending
from django.core.cache import cache

def can_send_email(user_email, email_type='general', limit=5, window=3600):
    """Check if user can send email (rate limiting)"""
    cache_key = f"email_limit:{email_type}:{user_email}"
    current_count = cache.get(cache_key, 0)
    
    if current_count >= limit:
        return False
    
    cache.set(cache_key, current_count + 1, window)
    return True
```

---

## 📧 Email Template Best Practices

### 1. **Template Structure**
```html
<!-- emails/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }} - {{ site_name }}</title>
    <style>
        /* Mobile-first responsive design */
        @media screen and (max-width: 600px) {
            .container { width: 100% !important; }
        }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
        {% include 'emails/footer.html' %}
    </div>
</body>
</html>
```

### 2. **Email Verification Template**
```html
<!-- emails/verify_email.html -->
{% extends 'emails/base.html' %}

{% block content %}
<div class="header">
    <h1>Welcome to {{ site_name }}!</h1>
    <p>Please verify your email address</p>
</div>

<div class="content">
    <h2>Hello {{ user.first_name|default:user.email }}!</h2>
    
    <p>Thank you for registering with {{ site_name }}. Please verify your email address:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ verification_url }}" 
           style="background: #007bff; color: white; padding: 15px 30px; 
                  text-decoration: none; border-radius: 5px; font-weight: bold;">
            Verify My Email
        </a>
    </div>
    
    <p>This link will expire in 24 hours.</p>
    
    <p>Best regards,<br>The {{ site_name }} Team</p>
</div>
{% endblock %}
```

---

## 🧪 Testing Email Configuration

### 1. **Test Script**
Create a test script to verify email configuration:

```python
# test_email.py
import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.development')
django.setup()

def test_email_sending():
    """Test email sending configuration"""
    try:
        send_mail(
            subject='Test Email from Bazary',
            message='This is a test email to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['your-email@example.com'],  # Change to your email
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

if __name__ == "__main__":
    test_email_sending()
```

### 2. **Django Shell Test**
```python
# Test in Django shell
python manage.py shell

from django.core.mail import send_mail
from django.conf import settings

# Test basic email
send_mail(
    'Test Subject',
    'Test message body',
    settings.DEFAULT_FROM_EMAIL,
    ['recipient@example.com'],
    fail_silently=False,
)

# Test user verification email
from apps.authentication.models import User
from apps.authentication.utils import create_email_verification_token, send_verification_email

user = User.objects.get(email='test@example.com')
token = create_email_verification_token(user)
result = send_verification_email(user, token)
print(f"Email sent: {result}")
```

---

## 🚀 Production Deployment

### 1. **Environment-Specific Configuration**
```python
# settings/production.py
from .base import *

# Production email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# Email security
EMAIL_TIMEOUT = 30
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# Logging for email debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django.mail': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 2. **Monitoring and Alerts**
```python
# Add email monitoring
import logging

logger = logging.getLogger('bazary.email')

def monitored_send_mail(**kwargs):
    """Send email with monitoring and error handling"""
    try:
        result = send_mail(**kwargs)
        logger.info(f"Email sent successfully to {kwargs.get('recipient_list')}")
        return result
    except Exception as e:
        logger.error(f"Email sending failed: {e}", extra={
            'recipient': kwargs.get('recipient_list'),
            'subject': kwargs.get('subject'),
            'error': str(e)
        })
        raise
```

---

## 📊 Email Analytics and Monitoring

### 1. **SendGrid Analytics**
- Open rates and click tracking
- Bounce and spam reporting
- Real-time email activity
- Detailed delivery statistics

### 2. **Custom Tracking**
```python
# Add custom email tracking
class EmailLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    recipient = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    opened = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_logs'
        indexes = [
            models.Index(fields=['user', 'email_type']),
            models.Index(fields=['sent_at']),
        ]
```

---

## 🎯 Next Steps

1. **Choose Email Service**: Select SendGrid, Mailgun, or SES based on your needs
2. **Configure Environment**: Set up API keys and domain authentication
3. **Test Configuration**: Run email tests in development environment
4. **Deploy to Production**: Configure production email settings
5. **Monitor Performance**: Set up analytics and error monitoring

---

## 📚 Resources

- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Mailgun Documentation](https://documentation.mailgun.com/)
- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Email Deliverability Best Practices](https://sendgrid.com/blog/email-deliverability-best-practices/)

---

*This guide will be updated as email services are configured and new features are added.*
