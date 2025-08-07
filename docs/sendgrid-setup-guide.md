# SendGrid Setup Guide for Bazary

## Current Issue
SendGrid requires **sender identity verification** before sending emails. The error you're seeing:
```
(550, b'The from address does not match a verified Sender Identity...')
```

This happens because `noreply@bazary.com` is not a verified sender identity.

## Solution Options

### Option 1: Single Sender Verification (Recommended for Development)

1. **Log into SendGrid Dashboard**: https://app.sendgrid.com/
2. **Navigate to Settings > Sender Authentication**
3. **Click "Verify a Single Sender"**
4. **Add your real email** (e.g., `legennd48@gmail.com`)
5. **Fill in the form**:
   - From Name: "Bazary Team"
   - From Email: `legennd48@gmail.com`
   - Reply To: `legennd48@gmail.com`
   - Company: "Bazary"
   - Address, City, etc. (required fields)
6. **Check your email and click the verification link**

#### Update Configuration
After verification, update your `.env.dev` file:

```bash
# Change this line:
DEFAULT_FROM_EMAIL=noreply@bazary.com

# To this:
DEFAULT_FROM_EMAIL=legennd48@gmail.com
```

### Option 2: Domain Authentication (Production)

For production, you'd need to:
1. Own a domain (e.g., buy `bazary-project.com`)
2. Set up DNS records to authenticate the domain
3. Use any email address from that domain

## Alternative Email Services

If SendGrid is too complex for development, consider these alternatives:

### 1. Gmail SMTP (Easiest for Development)
- Use your Gmail account
- Enable App Passwords
- No domain verification needed

### 2. Mailgun (Similar to SendGrid)
- Free tier: 100 emails/day
- Also requires domain verification
- Easier setup process

### 3. Console Backend (Development Only)
- No actual emails sent
- Perfect for development/testing
- Emails appear in terminal

## Quick Fix: Use Gmail SMTP

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security > App passwords
   - Generate password for "Mail"
3. **Update `.env.dev`**:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=legennd48@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
DEFAULT_FROM_EMAIL=legennd48@gmail.com
```

## Testing Commands

After any changes, test with:
```bash
cd /home/legennd/Software_repos/bazary
./bazary_env/bin/python scripts/test_email.py
```

## Recommendation

For **development**: Use Gmail SMTP (simplest)
For **production**: Use SendGrid with domain authentication

Would you like me to help set up Gmail SMTP instead?
