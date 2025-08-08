# Quick Email Configuration Guide

## Choose Your Email Backend

### Option 1: Gmail SMTP (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/
   - Security > 2-Step Verification > App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password

3. **Update `.env.dev`**:
```bash
# Gmail SMTP Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=legennd48@gmail.com
EMAIL_HOST_PASSWORD=your_16_character_app_password
DEFAULT_FROM_EMAIL=legennd48@gmail.com
```

### Option 2: Console Backend (Development Only)
```bash
# Console Backend (prints emails to terminal)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@bazary.com
```

### Option 3: SendGrid (After Verification)
```bash
# SendGrid Configuration (requires sender verification)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your_api_key_here
DEFAULT_FROM_EMAIL=your_verified_email@domain.com
```

## Test Command
After updating configuration:
```bash
cd /home/legennd/Software_repos/bazary
./bazary_env/bin/python scripts/test_email.py
```

Which option would you like to set up first?
