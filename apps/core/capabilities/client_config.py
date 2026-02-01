"""
Client Configuration System.

This module provides per-client/deployment configuration that works
alongside capabilities to customize the platform for each client.

Design:
- Each deployment has a client configuration
- Configuration is loaded from environment/settings
- Covers branding, locale, currency, tax rules, etc.
- Does NOT affect which capabilities are enabled (that's capabilities.py)
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings


@dataclass
class CurrencyConfig:
    """Currency configuration for a client."""
    code: str  # ISO 4217 code (e.g., "USD", "ETB")
    symbol: str  # Display symbol (e.g., "$", "Br")
    decimal_places: int = 2
    symbol_position: str = "before"  # "before" or "after"


@dataclass
class TaxConfig:
    """Tax configuration for a client."""
    enabled: bool = True
    default_rate: Decimal = Decimal("0.00")
    inclusive: bool = False  # Whether prices include tax
    tax_id_required: bool = False


@dataclass
class BrandingConfig:
    """Branding configuration for a client."""
    name: str = "Bazary"
    tagline: str = ""
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"


@dataclass
class LocaleConfig:
    """Locale configuration for a client."""
    default_language: str = "en"
    supported_languages: tuple = ("en",)
    timezone: str = "UTC"
    date_format: str = "Y-m-d"
    time_format: str = "H:i"


@dataclass
class NotificationConfig:
    """Notification configuration for a client."""
    email_enabled: bool = True
    sms_enabled: bool = False
    websocket_enabled: bool = True
    from_email: str = "noreply@bazary.com"
    from_name: str = "Bazary"


@dataclass
class ClientConfig:
    """
    Complete client configuration.
    
    This dataclass holds all per-client settings that customize
    the platform behavior without changing code.
    """
    # Client identification
    client_id: str = "default"
    client_name: str = "Default Client"
    
    # Feature configurations
    currency: CurrencyConfig = field(default_factory=lambda: CurrencyConfig(
        code="USD",
        symbol="$",
    ))
    tax: TaxConfig = field(default_factory=TaxConfig)
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    locale: LocaleConfig = field(default_factory=LocaleConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    
    # Business rules
    require_email_verification: bool = True
    allow_guest_checkout: bool = True
    max_cart_items: int = 100
    order_number_prefix: str = "ORD"
    booking_number_prefix: str = "BKG"
    
    # Operational settings
    support_email: str = ""
    support_phone: str = ""
    terms_url: str = ""
    privacy_url: str = ""
    
    @classmethod
    def from_settings(cls) -> "ClientConfig":
        """
        Load client configuration from Django settings.
        
        Settings should be structured as:
        CLIENT_CONFIG = {
            "client_id": "acme",
            "client_name": "Acme Corp",
            "currency": {"code": "USD", "symbol": "$"},
            ...
        }
        """
        config_dict = getattr(settings, "CLIENT_CONFIG", {})
        return cls.from_dict(config_dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientConfig":
        """Create ClientConfig from a dictionary."""
        # Parse nested configs
        currency_data = data.get("currency", {})
        currency = CurrencyConfig(
            code=currency_data.get("code", "USD"),
            symbol=currency_data.get("symbol", "$"),
            decimal_places=currency_data.get("decimal_places", 2),
            symbol_position=currency_data.get("symbol_position", "before"),
        )
        
        tax_data = data.get("tax", {})
        tax = TaxConfig(
            enabled=tax_data.get("enabled", True),
            default_rate=Decimal(str(tax_data.get("default_rate", "0.00"))),
            inclusive=tax_data.get("inclusive", False),
            tax_id_required=tax_data.get("tax_id_required", False),
        )
        
        branding_data = data.get("branding", {})
        branding = BrandingConfig(
            name=branding_data.get("name", "Bazary"),
            tagline=branding_data.get("tagline", ""),
            logo_url=branding_data.get("logo_url", ""),
            favicon_url=branding_data.get("favicon_url", ""),
            primary_color=branding_data.get("primary_color", "#007bff"),
            secondary_color=branding_data.get("secondary_color", "#6c757d"),
        )
        
        locale_data = data.get("locale", {})
        locale = LocaleConfig(
            default_language=locale_data.get("default_language", "en"),
            supported_languages=tuple(locale_data.get("supported_languages", ["en"])),
            timezone=locale_data.get("timezone", "UTC"),
            date_format=locale_data.get("date_format", "Y-m-d"),
            time_format=locale_data.get("time_format", "H:i"),
        )
        
        notif_data = data.get("notifications", {})
        notifications = NotificationConfig(
            email_enabled=notif_data.get("email_enabled", True),
            sms_enabled=notif_data.get("sms_enabled", False),
            websocket_enabled=notif_data.get("websocket_enabled", True),
            from_email=notif_data.get("from_email", "noreply@bazary.com"),
            from_name=notif_data.get("from_name", "Bazary"),
        )
        
        return cls(
            client_id=data.get("client_id", "default"),
            client_name=data.get("client_name", "Default Client"),
            currency=currency,
            tax=tax,
            branding=branding,
            locale=locale,
            notifications=notifications,
            require_email_verification=data.get("require_email_verification", True),
            allow_guest_checkout=data.get("allow_guest_checkout", True),
            max_cart_items=data.get("max_cart_items", 100),
            order_number_prefix=data.get("order_number_prefix", "ORD"),
            booking_number_prefix=data.get("booking_number_prefix", "BKG"),
            support_email=data.get("support_email", ""),
            support_phone=data.get("support_phone", ""),
            terms_url=data.get("terms_url", ""),
            privacy_url=data.get("privacy_url", ""),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API exposure."""
        return {
            "client_id": self.client_id,
            "client_name": self.client_name,
            "currency": {
                "code": self.currency.code,
                "symbol": self.currency.symbol,
                "decimal_places": self.currency.decimal_places,
                "symbol_position": self.currency.symbol_position,
            },
            "tax": {
                "enabled": self.tax.enabled,
                "default_rate": str(self.tax.default_rate),
                "inclusive": self.tax.inclusive,
            },
            "branding": {
                "name": self.branding.name,
                "tagline": self.branding.tagline,
                "logo_url": self.branding.logo_url,
                "primary_color": self.branding.primary_color,
                "secondary_color": self.branding.secondary_color,
            },
            "locale": {
                "default_language": self.locale.default_language,
                "supported_languages": list(self.locale.supported_languages),
                "timezone": self.locale.timezone,
            },
            "features": {
                "require_email_verification": self.require_email_verification,
                "allow_guest_checkout": self.allow_guest_checkout,
            },
            "support": {
                "email": self.support_email,
                "phone": self.support_phone,
                "terms_url": self.terms_url,
                "privacy_url": self.privacy_url,
            },
        }


# Singleton instance, lazily loaded
_client_config: Optional[ClientConfig] = None


def get_client_config() -> ClientConfig:
    """Get the current client configuration."""
    global _client_config
    if _client_config is None:
        _client_config = ClientConfig.from_settings()
    return _client_config


def reset_client_config() -> None:
    """Reset the client configuration (for testing)."""
    global _client_config
    _client_config = None
