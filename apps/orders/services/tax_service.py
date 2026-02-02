"""
Tax Calculation Service.

Provides tax calculation based on region, product category, and tax rules.
Supports multiple tax rates, tax exemptions, and compound taxes.
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
# Tax Rate Model
# ============================================================================

class TaxRate(TimeStampedModel):
    """
    Tax rate configuration model.
    
    Supports region-based tax rates with category overrides.
    """
    
    class TaxType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed Amount"
        COMPOUND = "compound", "Compound (applied after other taxes)"
    
    name = models.CharField(
        max_length=100,
        help_text="Tax name (e.g., 'VAT', 'Sales Tax', 'GST')",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique tax code",
    )
    description = models.TextField(
        blank=True,
        help_text="Tax description",
    )
    
    # Rate configuration
    tax_type = models.CharField(
        max_length=20,
        choices=TaxType.choices,
        default=TaxType.PERCENTAGE,
        help_text="Type of tax calculation",
    )
    rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal("0.00"),
        help_text="Tax rate (percentage or fixed amount)",
    )
    
    # Geographic scope
    country_code = models.CharField(
        max_length=2,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code",
    )
    state_province = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="State/Province (optional, for regional taxes)",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City (optional, for local taxes)",
    )
    postal_code_pattern = models.CharField(
        max_length=50,
        blank=True,
        help_text="Postal code pattern (regex) for tax applicability",
    )
    
    # Category-specific rules
    applies_to_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of category slugs this tax applies to (empty = all)",
    )
    excluded_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of category slugs exempt from this tax",
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tax rate is currently active",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Priority for applying multiple taxes (higher = applied first)",
    )
    is_included_in_price = models.BooleanField(
        default=False,
        help_text="Whether tax is already included in product prices",
    )
    
    # Validity period
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tax rate becomes effective",
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this tax rate expires",
    )
    
    class Meta:
        db_table = "tax_rates"
        ordering = ["-priority", "country_code", "state_province"]
        indexes = [
            models.Index(fields=["country_code", "state_province", "is_active"]),
        ]
    
    def __str__(self):
        location = self.country_code
        if self.state_province:
            location = f"{self.state_province}, {self.country_code}"
        return f"{self.name} ({self.rate}%) - {location}"
    
    @property
    def is_valid(self) -> bool:
        """Check if tax rate is currently valid."""
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return self.is_active


class TaxExemption(TimeStampedModel):
    """
    Tax exemption for specific users/businesses.
    """
    
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="tax_exemptions",
        help_text="User with tax exemption",
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.CASCADE,
        related_name="exemptions",
        null=True,
        blank=True,
        help_text="Specific tax rate exemption (null = all taxes)",
    )
    exemption_number = models.CharField(
        max_length=100,
        help_text="Tax exemption certificate/number",
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for exemption",
    )
    valid_from = models.DateField(
        help_text="Exemption start date",
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Exemption end date",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether exemption is active",
    )
    
    class Meta:
        db_table = "tax_exemptions"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Tax exemption for {self.user.email}"


# ============================================================================
# Tax Calculation Data Classes
# ============================================================================

@dataclass
class TaxLineItem:
    """Individual tax line item in a calculation."""
    tax_rate_id: str
    name: str
    rate: Decimal
    tax_type: str
    taxable_amount: Decimal
    tax_amount: Decimal
    is_included: bool = False


@dataclass
class TaxCalculation:
    """Result of a tax calculation."""
    subtotal: Decimal
    taxable_amount: Decimal
    total_tax: Decimal
    total_with_tax: Decimal
    tax_lines: List[TaxLineItem]
    exemptions_applied: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subtotal": str(self.subtotal),
            "taxable_amount": str(self.taxable_amount),
            "total_tax": str(self.total_tax),
            "total_with_tax": str(self.total_with_tax),
            "tax_lines": [
                {
                    "tax_rate_id": line.tax_rate_id,
                    "name": line.name,
                    "rate": str(line.rate),
                    "tax_type": line.tax_type,
                    "taxable_amount": str(line.taxable_amount),
                    "tax_amount": str(line.tax_amount),
                    "is_included": line.is_included,
                }
                for line in self.tax_lines
            ],
            "exemptions_applied": self.exemptions_applied,
        }


# ============================================================================
# Tax Service
# ============================================================================

class TaxService:
    """
    Service for calculating taxes.
    
    Supports:
    - Region-based tax rates (country, state, city, postal code)
    - Category-specific tax rules
    - Tax exemptions for users/businesses
    - Compound taxes (tax on tax)
    - Inclusive vs exclusive pricing
    """
    
    @classmethod
    def calculate_tax(
        cls,
        subtotal: Decimal,
        country_code: str,
        state_province: str = "",
        city: str = "",
        postal_code: str = "",
        category_slugs: List[str] = None,
        user=None,
    ) -> TaxCalculation:
        """
        Calculate applicable taxes for a purchase.
        
        Args:
            subtotal: Pre-tax amount
            country_code: ISO country code
            state_province: State/province code
            city: City name
            postal_code: Postal/ZIP code
            category_slugs: Product category slugs for category-specific taxes
            user: User instance for checking exemptions
            
        Returns:
            TaxCalculation with breakdown
        """
        subtotal = Decimal(str(subtotal))
        category_slugs = category_slugs or []
        
        # Get applicable tax rates
        tax_rates = cls._get_applicable_rates(
            country_code=country_code,
            state_province=state_province,
            city=city,
            postal_code=postal_code,
            category_slugs=category_slugs,
        )
        
        # Check for exemptions
        exemptions_applied = []
        if user:
            exemptions = cls._get_user_exemptions(user)
            exempt_rate_ids = {e.tax_rate_id for e in exemptions if e.tax_rate_id}
            has_full_exemption = any(e.tax_rate_id is None for e in exemptions)
            
            if has_full_exemption:
                # User is exempt from all taxes
                return TaxCalculation(
                    subtotal=subtotal,
                    taxable_amount=Decimal("0.00"),
                    total_tax=Decimal("0.00"),
                    total_with_tax=subtotal,
                    tax_lines=[],
                    exemptions_applied=["Full tax exemption"],
                )
            
            # Filter out exempt rates
            original_count = len(tax_rates)
            tax_rates = [r for r in tax_rates if str(r.id) not in exempt_rate_ids]
            if len(tax_rates) < original_count:
                exemptions_applied.append(f"Partial exemption ({original_count - len(tax_rates)} taxes)")
        
        # Calculate taxes
        tax_lines = []
        total_tax = Decimal("0.00")
        running_total = subtotal
        
        # Sort by priority (compound taxes applied last)
        regular_rates = [r for r in tax_rates if r.tax_type != TaxRate.TaxType.COMPOUND]
        compound_rates = [r for r in tax_rates if r.tax_type == TaxRate.TaxType.COMPOUND]
        
        # Apply regular taxes
        for rate in regular_rates:
            if rate.tax_type == TaxRate.TaxType.PERCENTAGE:
                tax_amount = (subtotal * rate.rate / Decimal("100")).quantize(Decimal("0.01"))
            else:  # Fixed amount
                tax_amount = rate.rate
            
            tax_lines.append(TaxLineItem(
                tax_rate_id=str(rate.id),
                name=rate.name,
                rate=rate.rate,
                tax_type=rate.tax_type,
                taxable_amount=subtotal,
                tax_amount=tax_amount,
                is_included=rate.is_included_in_price,
            ))
            
            if not rate.is_included_in_price:
                total_tax += tax_amount
        
        running_total = subtotal + total_tax
        
        # Apply compound taxes (on subtotal + other taxes)
        for rate in compound_rates:
            if rate.tax_type == TaxRate.TaxType.PERCENTAGE:
                # For compound, this shouldn't happen, but handle it
                tax_amount = (running_total * rate.rate / Decimal("100")).quantize(Decimal("0.01"))
            else:
                tax_amount = rate.rate
            
            tax_lines.append(TaxLineItem(
                tax_rate_id=str(rate.id),
                name=rate.name,
                rate=rate.rate,
                tax_type="compound",
                taxable_amount=running_total,
                tax_amount=tax_amount,
                is_included=rate.is_included_in_price,
            ))
            
            if not rate.is_included_in_price:
                total_tax += tax_amount
                running_total += tax_amount
        
        return TaxCalculation(
            subtotal=subtotal,
            taxable_amount=subtotal,
            total_tax=total_tax,
            total_with_tax=subtotal + total_tax,
            tax_lines=tax_lines,
            exemptions_applied=exemptions_applied,
        )
    
    @classmethod
    def _get_applicable_rates(
        cls,
        country_code: str,
        state_province: str = "",
        city: str = "",
        postal_code: str = "",
        category_slugs: List[str] = None,
    ) -> List[TaxRate]:
        """
        Get tax rates applicable to the given location and categories.
        """
        import re
        
        now = timezone.now()
        category_slugs = category_slugs or []
        
        # Base query for active rates
        rates = TaxRate.objects.filter(
            is_active=True,
            country_code=country_code,
        ).filter(
            models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
        )
        
        applicable_rates = []
        
        for rate in rates:
            # Check geographic scope (most specific wins)
            if rate.state_province and rate.state_province.lower() != state_province.lower():
                continue
            if rate.city and rate.city.lower() != city.lower():
                continue
            if rate.postal_code_pattern:
                if not re.match(rate.postal_code_pattern, postal_code):
                    continue
            
            # Check category applicability
            if rate.applies_to_categories and category_slugs:
                if not any(cat in rate.applies_to_categories for cat in category_slugs):
                    continue
            
            if rate.excluded_categories and category_slugs:
                if any(cat in rate.excluded_categories for cat in category_slugs):
                    continue
            
            applicable_rates.append(rate)
        
        # Sort by priority
        applicable_rates.sort(key=lambda r: -r.priority)
        
        return applicable_rates
    
    @classmethod
    def _get_user_exemptions(cls, user) -> List[TaxExemption]:
        """Get active tax exemptions for a user."""
        from django.utils import timezone
        today = timezone.now().date()
        
        return list(TaxExemption.objects.filter(
            user=user,
            is_active=True,
            valid_from__lte=today,
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=today)
        ))
    
    @classmethod
    def get_tax_summary_for_location(
        cls,
        country_code: str,
        state_province: str = "",
    ) -> Dict[str, Any]:
        """
        Get a summary of applicable taxes for a location.
        
        Useful for displaying estimated tax to users before checkout.
        """
        rates = cls._get_applicable_rates(
            country_code=country_code,
            state_province=state_province,
        )
        
        total_rate = sum(r.rate for r in rates if r.tax_type == TaxRate.TaxType.PERCENTAGE)
        
        return {
            "country_code": country_code,
            "state_province": state_province,
            "estimated_rate": str(total_rate),
            "tax_names": [r.name for r in rates],
            "rates": [
                {
                    "name": r.name,
                    "rate": str(r.rate),
                    "type": r.tax_type,
                    "included_in_price": r.is_included_in_price,
                }
                for r in rates
            ],
        }
    
    @classmethod
    def create_default_rates(cls) -> List[TaxRate]:
        """
        Create default tax rates for common regions.
        
        Call this during initial setup or migrations.
        """
        defaults = [
            # United States - Federal has no sales tax, states do
            {"name": "California Sales Tax", "code": "US-CA-SALES", "rate": Decimal("7.25"), "country_code": "US", "state_province": "CA"},
            {"name": "New York Sales Tax", "code": "US-NY-SALES", "rate": Decimal("8.00"), "country_code": "US", "state_province": "NY"},
            {"name": "Texas Sales Tax", "code": "US-TX-SALES", "rate": Decimal("6.25"), "country_code": "US", "state_province": "TX"},
            {"name": "Florida Sales Tax", "code": "US-FL-SALES", "rate": Decimal("6.00"), "country_code": "US", "state_province": "FL"},
            
            # European VAT
            {"name": "UK VAT", "code": "GB-VAT", "rate": Decimal("20.00"), "country_code": "GB", "state_province": ""},
            {"name": "Germany VAT", "code": "DE-VAT", "rate": Decimal("19.00"), "country_code": "DE", "state_province": ""},
            {"name": "France VAT", "code": "FR-VAT", "rate": Decimal("20.00"), "country_code": "FR", "state_province": ""},
            
            # Africa
            {"name": "Ethiopia VAT", "code": "ET-VAT", "rate": Decimal("15.00"), "country_code": "ET", "state_province": ""},
            {"name": "Kenya VAT", "code": "KE-VAT", "rate": Decimal("16.00"), "country_code": "KE", "state_province": ""},
            {"name": "Nigeria VAT", "code": "NG-VAT", "rate": Decimal("7.50"), "country_code": "NG", "state_province": ""},
            
            # Other
            {"name": "Canada GST", "code": "CA-GST", "rate": Decimal("5.00"), "country_code": "CA", "state_province": ""},
        ]
        
        created = []
        for data in defaults:
            rate, was_created = TaxRate.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "rate": data["rate"],
                    "country_code": data["country_code"],
                    "state_province": data.get("state_province", ""),
                    "tax_type": TaxRate.TaxType.PERCENTAGE,
                    "is_active": True,
                }
            )
            if was_created:
                created.append(rate)
        
        return created
