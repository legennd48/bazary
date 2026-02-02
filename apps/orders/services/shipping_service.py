"""
Shipping Calculation Service.

Provides shipping rate calculation based on:
- Shipping zones and regions
- Package weight and dimensions
- Shipping methods (standard, express, overnight)
- Free shipping thresholds
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional
import logging

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

logger = logging.getLogger(__name__)


# ============================================================================
# Shipping Zone Model
# ============================================================================

class ShippingZone(TimeStampedModel):
    """
    Shipping zone model.
    
    Groups countries/regions with similar shipping rates.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Zone name (e.g., 'Domestic', 'Europe', 'International')",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique zone code",
    )
    description = models.TextField(
        blank=True,
        help_text="Zone description",
    )
    countries = models.JSONField(
        default=list,
        help_text="List of ISO country codes in this zone",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this zone is active",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Priority for matching (higher = checked first)",
    )
    
    class Meta:
        db_table = "shipping_zones"
        ordering = ["-priority", "name"]
    
    def __str__(self):
        return f"{self.name} ({len(self.countries)} countries)"


class ShippingMethod(TimeStampedModel):
    """
    Shipping method model.
    
    Defines available shipping options and their base costs.
    """
    
    class MethodType(models.TextChoices):
        FLAT_RATE = "flat_rate", "Flat Rate"
        WEIGHT_BASED = "weight_based", "Weight Based"
        PRICE_BASED = "price_based", "Price Based"
        CARRIER_CALCULATED = "carrier_calculated", "Carrier Calculated"
        FREE = "free", "Free Shipping"
        LOCAL_PICKUP = "local_pickup", "Local Pickup"
    
    name = models.CharField(
        max_length=100,
        help_text="Method name (e.g., 'Standard Shipping', 'Express')",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique method code",
    )
    description = models.TextField(
        blank=True,
        help_text="Method description",
    )
    method_type = models.CharField(
        max_length=20,
        choices=MethodType.choices,
        default=MethodType.FLAT_RATE,
        help_text="Type of rate calculation",
    )
    
    # Base pricing
    base_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Base shipping rate",
    )
    
    # Weight-based pricing
    rate_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Additional rate per kg (for weight-based)",
    )
    min_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Minimum weight for this method",
    )
    max_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum weight for this method",
    )
    
    # Price-based thresholds
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Minimum order amount for this method",
    )
    max_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum order amount for this method",
    )
    
    # Delivery estimates
    min_delivery_days = models.PositiveIntegerField(
        default=3,
        help_text="Minimum estimated delivery days",
    )
    max_delivery_days = models.PositiveIntegerField(
        default=7,
        help_text="Maximum estimated delivery days",
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this method is available",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Display priority (higher = shown first)",
    )
    
    class Meta:
        db_table = "shipping_methods"
        ordering = ["-priority", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.method_type})"


class ShippingRate(TimeStampedModel):
    """
    Zone-specific shipping rate model.
    
    Links shipping methods to zones with specific pricing.
    """
    
    zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.CASCADE,
        related_name="rates",
        help_text="Shipping zone",
    )
    method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.CASCADE,
        related_name="zone_rates",
        help_text="Shipping method",
    )
    
    # Override pricing for this zone
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Shipping rate for this zone/method combination",
    )
    rate_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Additional rate per kg for this zone",
    )
    
    # Free shipping threshold for this zone
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Order amount for free shipping (null = no free shipping)",
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rate is active",
    )
    
    class Meta:
        db_table = "shipping_rates"
        unique_together = ["zone", "method"]
        ordering = ["zone", "method"]
    
    def __str__(self):
        return f"{self.method.name} to {self.zone.name}: ${self.rate}"


# ============================================================================
# Shipping Calculation Data Classes
# ============================================================================

@dataclass
class ShippingOption:
    """A shipping option available to the customer."""
    method_id: str
    method_code: str
    name: str
    description: str
    rate: Decimal
    is_free: bool
    min_delivery_days: int
    max_delivery_days: int
    delivery_estimate: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_id": self.method_id,
            "method_code": self.method_code,
            "name": self.name,
            "description": self.description,
            "rate": str(self.rate),
            "is_free": self.is_free,
            "min_delivery_days": self.min_delivery_days,
            "max_delivery_days": self.max_delivery_days,
            "delivery_estimate": self.delivery_estimate,
        }


@dataclass
class ShippingCalculation:
    """Result of a shipping calculation."""
    country_code: str
    zone_name: str
    subtotal: Decimal
    weight_kg: Decimal
    selected_method: Optional[ShippingOption]
    available_options: List[ShippingOption]
    shipping_cost: Decimal
    is_free_shipping: bool
    free_shipping_threshold: Optional[Decimal]
    amount_to_free_shipping: Optional[Decimal]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "country_code": self.country_code,
            "zone_name": self.zone_name,
            "subtotal": str(self.subtotal),
            "weight_kg": str(self.weight_kg),
            "selected_method": self.selected_method.to_dict() if self.selected_method else None,
            "available_options": [opt.to_dict() for opt in self.available_options],
            "shipping_cost": str(self.shipping_cost),
            "is_free_shipping": self.is_free_shipping,
            "free_shipping_threshold": str(self.free_shipping_threshold) if self.free_shipping_threshold else None,
            "amount_to_free_shipping": str(self.amount_to_free_shipping) if self.amount_to_free_shipping else None,
        }


# ============================================================================
# Shipping Service
# ============================================================================

class ShippingService:
    """
    Service for calculating shipping rates.
    
    Supports:
    - Zone-based shipping rates
    - Multiple shipping methods per zone
    - Weight-based pricing
    - Free shipping thresholds
    - Delivery time estimates
    """
    
    @classmethod
    def calculate_shipping(
        cls,
        country_code: str,
        subtotal: Decimal,
        weight_kg: Decimal = Decimal("0.00"),
        selected_method_code: str = None,
    ) -> ShippingCalculation:
        """
        Calculate available shipping options for a destination.
        
        Args:
            country_code: ISO country code
            subtotal: Order subtotal (for free shipping calculation)
            weight_kg: Total package weight in kg
            selected_method_code: Pre-selected shipping method code
            
        Returns:
            ShippingCalculation with all options and selected rate
        """
        subtotal = Decimal(str(subtotal))
        weight_kg = Decimal(str(weight_kg))
        
        # Find the zone for this country
        zone = cls._get_zone_for_country(country_code)
        
        if not zone:
            # No zone found - return default/fallback
            return ShippingCalculation(
                country_code=country_code,
                zone_name="Unknown",
                subtotal=subtotal,
                weight_kg=weight_kg,
                selected_method=None,
                available_options=[],
                shipping_cost=Decimal("0.00"),
                is_free_shipping=False,
                free_shipping_threshold=None,
                amount_to_free_shipping=None,
            )
        
        # Get available rates for this zone
        rates = ShippingRate.objects.filter(
            zone=zone,
            is_active=True,
            method__is_active=True,
        ).select_related("method").order_by("-method__priority")
        
        available_options = []
        selected_option = None
        lowest_free_threshold = None
        
        for rate in rates:
            method = rate.method
            
            # Check weight limits
            if method.max_weight_kg and weight_kg > method.max_weight_kg:
                continue
            if weight_kg < method.min_weight_kg:
                continue
            
            # Check order amount limits
            if subtotal < method.min_order_amount:
                continue
            if method.max_order_amount and subtotal > method.max_order_amount:
                continue
            
            # Calculate rate
            shipping_rate = rate.rate
            
            # Add weight-based charges
            if method.method_type == ShippingMethod.MethodType.WEIGHT_BASED and weight_kg > 0:
                shipping_rate += rate.rate_per_kg * weight_kg
            
            # Check for free shipping
            is_free = False
            if method.method_type == ShippingMethod.MethodType.FREE:
                is_free = True
                shipping_rate = Decimal("0.00")
            elif rate.free_shipping_threshold and subtotal >= rate.free_shipping_threshold:
                is_free = True
                shipping_rate = Decimal("0.00")
            
            # Track lowest free shipping threshold
            if rate.free_shipping_threshold:
                if lowest_free_threshold is None or rate.free_shipping_threshold < lowest_free_threshold:
                    lowest_free_threshold = rate.free_shipping_threshold
            
            # Build delivery estimate string
            if method.min_delivery_days == method.max_delivery_days:
                delivery_estimate = f"{method.min_delivery_days} business days"
            else:
                delivery_estimate = f"{method.min_delivery_days}-{method.max_delivery_days} business days"
            
            option = ShippingOption(
                method_id=str(method.id),
                method_code=method.code,
                name=method.name,
                description=method.description,
                rate=shipping_rate.quantize(Decimal("0.01")),
                is_free=is_free,
                min_delivery_days=method.min_delivery_days,
                max_delivery_days=method.max_delivery_days,
                delivery_estimate=delivery_estimate,
            )
            
            available_options.append(option)
            
            # Select this option if it matches requested method
            if selected_method_code and method.code == selected_method_code:
                selected_option = option
        
        # If no method selected, pick the cheapest
        if not selected_option and available_options:
            selected_option = min(available_options, key=lambda o: o.rate)
        
        # Calculate amount to free shipping
        amount_to_free = None
        if lowest_free_threshold and subtotal < lowest_free_threshold:
            amount_to_free = lowest_free_threshold - subtotal
        
        return ShippingCalculation(
            country_code=country_code,
            zone_name=zone.name,
            subtotal=subtotal,
            weight_kg=weight_kg,
            selected_method=selected_option,
            available_options=available_options,
            shipping_cost=selected_option.rate if selected_option else Decimal("0.00"),
            is_free_shipping=selected_option.is_free if selected_option else False,
            free_shipping_threshold=lowest_free_threshold,
            amount_to_free_shipping=amount_to_free,
        )
    
    @classmethod
    def _get_zone_for_country(cls, country_code: str) -> Optional[ShippingZone]:
        """Find the shipping zone containing a country."""
        zones = ShippingZone.objects.filter(
            is_active=True,
        ).order_by("-priority")
        
        for zone in zones:
            if country_code.upper() in [c.upper() for c in zone.countries]:
                return zone
        
        return None
    
    @classmethod
    def get_available_methods(
        cls,
        country_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all available shipping methods for a country.
        
        Useful for displaying options before cart totals are known.
        """
        zone = cls._get_zone_for_country(country_code)
        
        if not zone:
            return []
        
        rates = ShippingRate.objects.filter(
            zone=zone,
            is_active=True,
            method__is_active=True,
        ).select_related("method").order_by("-method__priority")
        
        return [
            {
                "code": rate.method.code,
                "name": rate.method.name,
                "description": rate.method.description,
                "base_rate": str(rate.rate),
                "free_shipping_threshold": str(rate.free_shipping_threshold) if rate.free_shipping_threshold else None,
                "delivery_estimate": f"{rate.method.min_delivery_days}-{rate.method.max_delivery_days} days",
            }
            for rate in rates
        ]
    
    @classmethod
    def create_default_zones_and_methods(cls) -> Dict[str, Any]:
        """
        Create default shipping zones and methods.
        
        Call during initial setup.
        """
        # Create zones
        zones_data = [
            {
                "name": "Domestic (Ethiopia)", 
                "code": "ET-DOMESTIC",
                "countries": ["ET"],
                "priority": 100,
            },
            {
                "name": "East Africa",
                "code": "EAST-AFRICA", 
                "countries": ["KE", "UG", "TZ", "RW", "BI", "SS", "SO", "DJ", "ER"],
                "priority": 50,
            },
            {
                "name": "Africa",
                "code": "AFRICA",
                "countries": ["NG", "GH", "ZA", "EG", "MA", "DZ", "TN", "SN", "CI", "CM", "CD", "AO", "MZ", "ZW", "ZM", "MW", "BW", "NA", "LS", "SZ"],
                "priority": 40,
            },
            {
                "name": "Europe",
                "code": "EUROPE",
                "countries": ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "PT", "AT", "CH", "SE", "NO", "DK", "FI", "IE", "PL", "CZ", "HU", "RO", "GR"],
                "priority": 30,
            },
            {
                "name": "North America",
                "code": "NORTH-AMERICA",
                "countries": ["US", "CA", "MX"],
                "priority": 30,
            },
            {
                "name": "International",
                "code": "INTERNATIONAL",
                "countries": [],  # Catch-all
                "priority": 0,
            },
        ]
        
        zones = {}
        for data in zones_data:
            zone, _ = ShippingZone.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "countries": data["countries"],
                    "priority": data["priority"],
                    "is_active": True,
                }
            )
            zones[data["code"]] = zone
        
        # Create methods
        methods_data = [
            {
                "name": "Standard Shipping",
                "code": "STANDARD",
                "method_type": ShippingMethod.MethodType.FLAT_RATE,
                "min_delivery_days": 5,
                "max_delivery_days": 10,
                "priority": 10,
            },
            {
                "name": "Express Shipping",
                "code": "EXPRESS",
                "method_type": ShippingMethod.MethodType.FLAT_RATE,
                "min_delivery_days": 2,
                "max_delivery_days": 4,
                "priority": 20,
            },
            {
                "name": "Overnight Shipping",
                "code": "OVERNIGHT",
                "method_type": ShippingMethod.MethodType.FLAT_RATE,
                "min_delivery_days": 1,
                "max_delivery_days": 2,
                "priority": 30,
            },
            {
                "name": "Free Shipping",
                "code": "FREE",
                "method_type": ShippingMethod.MethodType.FREE,
                "min_delivery_days": 7,
                "max_delivery_days": 14,
                "priority": 5,
                "min_order_amount": Decimal("50.00"),
            },
            {
                "name": "Local Pickup",
                "code": "PICKUP",
                "method_type": ShippingMethod.MethodType.LOCAL_PICKUP,
                "min_delivery_days": 0,
                "max_delivery_days": 1,
                "priority": 40,
            },
        ]
        
        methods = {}
        for data in methods_data:
            method, _ = ShippingMethod.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "method_type": data["method_type"],
                    "min_delivery_days": data["min_delivery_days"],
                    "max_delivery_days": data["max_delivery_days"],
                    "priority": data["priority"],
                    "min_order_amount": data.get("min_order_amount", Decimal("0.00")),
                    "is_active": True,
                }
            )
            methods[data["code"]] = method
        
        # Create zone rates
        rates_data = [
            # Domestic Ethiopia
            {"zone": "ET-DOMESTIC", "method": "STANDARD", "rate": Decimal("5.00"), "free_threshold": Decimal("30.00")},
            {"zone": "ET-DOMESTIC", "method": "EXPRESS", "rate": Decimal("10.00"), "free_threshold": Decimal("75.00")},
            {"zone": "ET-DOMESTIC", "method": "PICKUP", "rate": Decimal("0.00"), "free_threshold": None},
            
            # East Africa
            {"zone": "EAST-AFRICA", "method": "STANDARD", "rate": Decimal("12.00"), "free_threshold": Decimal("75.00")},
            {"zone": "EAST-AFRICA", "method": "EXPRESS", "rate": Decimal("25.00"), "free_threshold": Decimal("150.00")},
            
            # Africa
            {"zone": "AFRICA", "method": "STANDARD", "rate": Decimal("20.00"), "free_threshold": Decimal("100.00")},
            {"zone": "AFRICA", "method": "EXPRESS", "rate": Decimal("40.00"), "free_threshold": Decimal("200.00")},
            
            # Europe
            {"zone": "EUROPE", "method": "STANDARD", "rate": Decimal("25.00"), "free_threshold": Decimal("150.00")},
            {"zone": "EUROPE", "method": "EXPRESS", "rate": Decimal("50.00"), "free_threshold": Decimal("300.00")},
            
            # North America
            {"zone": "NORTH-AMERICA", "method": "STANDARD", "rate": Decimal("30.00"), "free_threshold": Decimal("150.00")},
            {"zone": "NORTH-AMERICA", "method": "EXPRESS", "rate": Decimal("60.00"), "free_threshold": Decimal("300.00")},
        ]
        
        created_rates = []
        for data in rates_data:
            if data["zone"] in zones and data["method"] in methods:
                rate, _ = ShippingRate.objects.update_or_create(
                    zone=zones[data["zone"]],
                    method=methods[data["method"]],
                    defaults={
                        "rate": data["rate"],
                        "free_shipping_threshold": data["free_threshold"],
                        "is_active": True,
                    }
                )
                created_rates.append(rate)
        
        return {
            "zones_created": len(zones),
            "methods_created": len(methods),
            "rates_created": len(created_rates),
        }
