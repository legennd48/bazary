#!/usr/bin/env python
"""
Email service test script for SendGrid integration.
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from apps.authentication.models import User
from apps.authentication.utils import create_email_verification_token, send_verification_email


def test_basic_email():
    """Test basic Django email functionality."""
    print("🧪 Testing basic email sending...")
    
    try:
        result = send_mail(
            subject='Bazary Email Test',
            message='This is a test email from Bazary using SendGrid!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],  # Replace with your email
            fail_silently=False,
        )
        print(f"✅ Basic email test successful! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Basic email test failed: {e}")
        return False


def test_verification_email():
    """Test email verification system."""
    print("\n🧪 Testing email verification system...")
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email='test.user@example.com',  # Replace with your email
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'test.user@example.com'
            }
        )
        
        if created:
            user.set_password('TestPass123!')
            user.save()
            print(f"✅ Created test user: {user.email}")
        else:
            print(f"📧 Using existing test user: {user.email}")
        
        # Create verification token
        token = create_email_verification_token(user)
        print(f"✅ Created verification token: {token.token[:20]}...")
        
        # Send verification email
        result = send_verification_email(user, token)
        if result:
            print("✅ Verification email sent successfully!")
            return True
        else:
            print("❌ Failed to send verification email")
            return False
            
    except Exception as e:
        print(f"❌ Verification email test failed: {e}")
        return False


def test_email_configuration():
    """Test email configuration."""
    print("\n⚙️ Email Configuration:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"SENDGRID_API_KEY: {'*' * 20}{settings.SENDGRID_API_KEY[-10:] if hasattr(settings, 'SENDGRID_API_KEY') else 'Not set'}")


if __name__ == "__main__":
    print("🚀 Bazary Email Service Test")
    print("=" * 50)
    
    # Test configuration
    test_email_configuration()
    
    # Test basic email
    basic_success = test_basic_email()
    
    # Test verification email
    verification_success = test_verification_email()
    
    print("\n📊 Test Results:")
    print(f"Basic Email: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Verification Email: {'✅ PASS' if verification_success else '❌ FAIL'}")
    
    if basic_success and verification_success:
        print("\n🎉 All email tests passed! SendGrid integration is working!")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
        
    print("\n📝 Next Steps:")
    print("1. Check your email inbox for test emails")
    print("2. Verify the verification email has the correct links")
    print("3. Update the recipient email addresses to your actual email")

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def test_basic_email(recipient_email):
    """Test basic email sending functionality."""
    print("🧪 Testing basic email sending...")
    
    try:
        result = send_mail(
            subject='🎉 Bazary Email Configuration Test',
            message='This is a test email to verify your email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        if result:
            print("✅ Basic email sent successfully!")
            return True
        else:
            print("❌ Email sending failed - no result returned")
            return False
            
    except Exception as e:
        print(f"❌ Email sending failed with error: {e}")
        return False


def test_html_email(recipient_email):
    """Test HTML email with template."""
    print("🧪 Testing HTML email with template...")
    
    try:
        # Create test context
        context = {
            'user_name': 'Test User',
            'site_name': settings.SITE_NAME,
            'test_url': f"{settings.FRONTEND_URL}/test",
            'current_year': 2025,
        }
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Test - {context['site_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #f8f9fa; padding: 30px; border-radius: 8px; }}
                .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: white; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 14px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Email Configuration Test</h1>
                </div>
                <div class="content">
                    <h2>Hello {context['user_name']}!</h2>
                    <p>Congratulations! Your email configuration for <strong>{context['site_name']}</strong> is working perfectly.</p>
                    
                    <p>This test email confirms that:</p>
                    <ul>
                        <li>✅ SMTP settings are configured correctly</li>
                        <li>✅ HTML emails are rendering properly</li>
                        <li>✅ Email templates are working</li>
                        <li>✅ Your email service is operational</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="{context['test_url']}" class="button">Visit {context['site_name']}</a>
                    </div>
                    
                    <p>You're now ready to send user verification emails, password resets, and other notifications!</p>
                    
                    <p>Best regards,<br>The {context['site_name']} Development Team</p>
                </div>
                <div class="footer">
                    <p>© {context['current_year']} {context['site_name']} - E-commerce Platform</p>
                    <p>This is a test email for configuration verification.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_content = strip_tags(html_content)
        
        result = send_mail(
            subject=f'🎨 {context["site_name"]} - HTML Email Template Test',
            message=plain_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False,
        )
        
        if result:
            print("✅ HTML email sent successfully!")
            return True
        else:
            print("❌ HTML email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ HTML email sending failed with error: {e}")
        return False


def test_user_verification_email():
    """Test the actual user verification email workflow."""
    print("🧪 Testing user verification email workflow...")
    
    try:
        from apps.authentication.models import User
        from apps.authentication.utils import create_email_verification_token, send_verification_email
        
        # Get or create test user
        test_email = "test-verification@example.com"
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'username': test_email,
            }
        )
        
        if created:
            user.set_password('TestPassword123!')
            user.save()
            print(f"📝 Created test user: {test_email}")
        else:
            print(f"📝 Using existing test user: {test_email}")
        
        # Create verification token
        token = create_email_verification_token(user)
        print(f"🔑 Created verification token: {token.token[:20]}...")
        
        # Send verification email
        result = send_verification_email(user, token)
        
        if result:
            print("✅ User verification email sent successfully!")
            print(f"📧 Verification link: {settings.FRONTEND_URL}/verify-email?token={token.token}")
            return True
        else:
            print("❌ User verification email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ User verification email failed with error: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("📧 BAZARY EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Display current configuration
    print(f"📋 Current email settings:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
    print(f"   Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
    print(f"   Use TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not configured')}")
    print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   Site Name: {getattr(settings, 'SITE_NAME', 'Not configured')}")
    print(f"   Frontend URL: {getattr(settings, 'FRONTEND_URL', 'Not configured')}")
    print()
    
    # Get recipient email
    recipient = input("📧 Enter your email address to test email sending: ").strip()
    
    if not recipient or '@' not in recipient:
        print("❌ Invalid email address provided. Exiting.")
        return
    
    print(f"📤 Sending test emails to: {recipient}")
    print()
    
    # Run tests
    test_results = []
    
    # Test 1: Basic email
    test_results.append(test_basic_email(recipient))
    print()
    
    # Test 2: HTML email
    test_results.append(test_html_email(recipient))
    print()
    
    # Test 3: User verification email
    test_results.append(test_user_verification_email())
    print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    tests = [
        "Basic Email Sending",
        "HTML Email Template", 
        "User Verification Email"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, test_results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {test_name}: {status}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    
    print()
    if success_count == total_count:
        print("🎉 ALL TESTS PASSED! Your email configuration is working perfectly.")
        print("🚀 You're ready to use email features in production!")
    else:
        print(f"⚠️  {success_count}/{total_count} tests passed. Please check your email configuration.")
        print("💡 Refer to docs/email-service-setup.md for configuration help.")
    
    print()
    print("🔧 Next steps:")
    print("1. If using console backend, check your terminal for email output")
    print("2. If using SMTP, check your email inbox")
    print("3. Configure SendGrid/Mailgun for production use")
    print("4. Update environment variables with your API keys")


if __name__ == "__main__":
    main()
