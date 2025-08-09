"""
Django management command to set up payment providers.

This command configures payment providers (like Chapa) with API credentials
from environment variables.
"""

import logging
import os
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.payments.models import PaymentProvider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Set up payment providers with credentials from environment variables.

    Usage:
        python manage.py setup_payment_providers
        python manage.py setup_payment_providers --provider chapa
        python manage.py setup_payment_providers --test-mode
        python manage.py setup_payment_providers --force  # Override existing
    """

    help = "Set up payment providers with API credentials from environment variables"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--provider",
            type=str,
            choices=["chapa", "all"],
            default="all",
            help="Specific provider to set up (default: all)",
        )
        parser.add_argument(
            "--test-mode",
            action="store_true",
            help="Configure providers in test mode",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Override existing provider configurations",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        """Execute the payment provider setup."""
        start_time = timezone.now()

        self.stdout.write(self.style.SUCCESS("🔧 Setting up payment providers..."))

        if options["verbose"]:
            self.stdout.write("Configuration:")
            self.stdout.write(f"  - Provider: {options['provider']}")
            self.stdout.write(f"  - Test mode: {options['test_mode']}")
            self.stdout.write(f"  - Force override: {options['force']}")

        try:
            with transaction.atomic():
                providers_configured = 0

                if options["provider"] in ["chapa", "all"]:
                    if self.setup_chapa_provider(options):
                        providers_configured += 1

                if providers_configured == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "⚠️ No providers were configured. Check environment variables."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Successfully configured {providers_configured} payment provider(s)"
                        )
                    )

                self.display_summary()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Provider setup failed: {str(e)}")
            )
            raise CommandError(f"Failed to set up payment providers: {str(e)}")

        duration = timezone.now() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Payment provider setup completed in {duration.total_seconds():.2f} seconds!"
            )
        )

    def setup_chapa_provider(self, options: Dict[str, Any]) -> bool:
        """
        Set up Chapa payment provider.
        
        Returns:
            bool: True if provider was configured, False otherwise
        """
        verbose = options.get("verbose", False)
        test_mode = options.get("test_mode", False)
        force = options.get("force", False)

        if verbose:
            self.stdout.write("🇪🇹 Setting up Chapa payment provider...")

        # Check for required environment variables
        required_vars = {
            "public_key": os.getenv("CHAPA_PUBLIC_KEY"),
            "secret_key": os.getenv("CHAPA_SECRET_KEY"),
            "encryption_key": os.getenv("CHAPA_ENCRYPTION_KEY"),
        }

        missing_vars = [
            var_name for var_name, value in required_vars.items() if not value
        ]

        if missing_vars:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Missing Chapa environment variables: {', '.join(missing_vars)}"
                )
            )
            self.stdout.write("Required variables:")
            self.stdout.write("  - CHAPA_PUBLIC_KEY")
            self.stdout.write("  - CHAPA_SECRET_KEY")
            self.stdout.write("  - CHAPA_ENCRYPTION_KEY")
            return False

        # Check if provider already exists
        existing_provider = PaymentProvider.objects.filter(
            provider_type=PaymentProvider.ProviderType.CHAPA
        ).first()

        if existing_provider and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Chapa provider already exists (ID: {existing_provider.id}). "
                    "Use --force to override."
                )
            )
            if verbose:
                self.stdout.write(f"  Current config:")
                self.stdout.write(f"    - Name: {existing_provider.name}")
                self.stdout.write(f"    - Active: {existing_provider.is_active}")
                self.stdout.write(f"    - Test mode: {existing_provider.test_mode}")
            return False

        # Create or update provider
        provider_data = {
            "name": "Chapa Payment Gateway",
            "provider_type": PaymentProvider.ProviderType.CHAPA,
            "api_key": required_vars["public_key"],
            "secret_key": required_vars["secret_key"],
            "webhook_secret": required_vars["encryption_key"],
            "is_active": True,
            "test_mode": test_mode,
            "configuration": {
                "currency": "ETB",
                "webhook_url": "/api/v1/payments/webhooks/chapa/",
                "return_url": "/payments/success/",
                "cancel_url": "/payments/cancel/",
                "logo_url": "",
                "description": "Ethiopian payment gateway for local transactions",
            },
        }

        if existing_provider:
            # Update existing provider
            for key, value in provider_data.items():
                setattr(existing_provider, key, value)
            existing_provider.save()
            provider = existing_provider
            action = "Updated"
        else:
            # Create new provider
            provider = PaymentProvider.objects.create(**provider_data)
            action = "Created"

        if verbose:
            self.stdout.write(f"  ✓ {action} Chapa provider:")
            self.stdout.write(f"    - ID: {provider.id}")
            self.stdout.write(f"    - Name: {provider.name}")
            self.stdout.write(f"    - Test mode: {provider.test_mode}")
            self.stdout.write(f"    - Active: {provider.is_active}")
            self.stdout.write(f"    - API Key: {provider.api_key[:8]}...")
            self.stdout.write(f"    - Webhook Secret: {provider.webhook_secret[:8]}...")

        self.stdout.write(
            self.style.SUCCESS(f"✅ {action} Chapa payment provider")
        )
        return True

    def display_summary(self):
        """Display current payment provider status."""
        self.stdout.write("\n📊 Payment Providers Summary:")
        
        providers = PaymentProvider.objects.all()
        if not providers.exists():
            self.stdout.write("  No payment providers configured")
            return

        for provider in providers:
            status_icon = "✅" if provider.is_active else "❌"
            mode_text = "TEST" if provider.test_mode else "LIVE"
            
            self.stdout.write(
                f"  {status_icon} {provider.get_provider_type_display()} "
                f"({mode_text}) - {provider.name}"
            )
            
            if provider.provider_type == PaymentProvider.ProviderType.CHAPA:
                self.stdout.write(f"    - Currency: ETB (Ethiopian Birr)")
                self.stdout.write(f"    - Webhook: {provider.configuration.get('webhook_url', 'Not set')}")

        # Show configuration tips
        self.stdout.write("\n💡 Next Steps:")
        self.stdout.write("  1. Verify provider credentials in Django admin")
        self.stdout.write("  2. Test payment flow in test mode first")
        self.stdout.write("  3. Configure webhook URLs in provider dashboard")
        self.stdout.write("  4. Switch to live mode when ready for production")
