"""
Product filters for advanced search and filtering.
"""

from django.db.models import F, Q

import django_filters

from apps.categories.models import Category

from .models import Product, Tag


class ProductFilter(django_filters.FilterSet):
    """
    Advanced filtering for products.
    """

    # Price range filters
    price_min = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", help_text="Minimum price"
    )
    price_max = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", help_text="Maximum price"
    )

    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(), help_text="Filter by category"
    )
    category_slug = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        help_text="Filter by category slug",
    )

    # Tag filters
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        conjoined=False,  # OR operation instead of AND
        help_text="Filter by tags",
    )
    tag_names = django_filters.CharFilter(
        method="filter_by_tag_names", help_text="Filter by tag names (comma-separated)"
    )

    # Stock filters
    in_stock = django_filters.BooleanFilter(
        method="filter_in_stock", help_text="Filter products in stock"
    )
    low_stock = django_filters.BooleanFilter(
        method="filter_low_stock", help_text="Filter products with low stock"
    )

    # Status filters
    is_featured = django_filters.BooleanFilter(help_text="Filter featured products")
    is_active = django_filters.BooleanFilter(help_text="Filter active products")
    is_digital = django_filters.BooleanFilter(help_text="Filter digital products")

    # Date filters
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        help_text="Filter products created after this date",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        help_text="Filter products created before this date",
    )

    # Search filters
    search = django_filters.CharFilter(
        method="filter_search", help_text="Search in name, description, and SKU"
    )

    class Meta:
        model = Product
        fields = {
            "name": ["icontains", "exact"],
            "sku": ["icontains", "exact"],
            "price": ["exact", "gte", "lte"],
            "stock_quantity": ["exact", "gte", "lte"],
            "is_active": ["exact"],
            "is_featured": ["exact"],
            "is_digital": ["exact"],
        }

    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock."""
        if value is True:
            return queryset.filter(Q(track_inventory=False) | Q(stock_quantity__gt=0))
        elif value is False:
            return queryset.filter(track_inventory=True, stock_quantity=0)
        return queryset

    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock."""
        if value is True:
            return queryset.filter(
                track_inventory=True, stock_quantity__lte=F("low_stock_threshold")
            )
        elif value is False:
            return queryset.filter(
                Q(track_inventory=False)
                | Q(stock_quantity__gt=F("low_stock_threshold"))
            )
        return queryset

    def filter_by_tag_names(self, queryset, name, value):
        """Filter by tag names (comma-separated)."""
        if not value:
            return queryset

        tag_names = [tag.strip() for tag in value.split(",") if tag.strip()]
        if tag_names:
            return queryset.filter(tags__name__in=tag_names).distinct()
        return queryset

    def filter_search(self, queryset, name, value):
        """
        Advanced search across multiple fields.
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(short_description__icontains=value)
            | Q(sku__icontains=value)
            | Q(tags__name__icontains=value)
        ).distinct()


class TagFilter(django_filters.FilterSet):
    """
    Filtering for tags.
    """

    name = django_filters.CharFilter(
        lookup_expr="icontains", help_text="Filter by tag name"
    )

    color = django_filters.CharFilter(
        lookup_expr="exact", help_text="Filter by tag color"
    )

    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        help_text="Filter tags created after this date",
    )

    class Meta:
        model = Tag
        fields = ["name", "color"]
