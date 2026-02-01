"""
Service Views.

ViewSets for service management with full CRUD and provider assignment.
"""

from django.db.models import Count, Q
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.core.capabilities.registry import require_capability

from .models import (
    Service,
    ServiceAddon,
    ServiceCategory,
    ServiceImage,
    ServiceProvider,
    ServiceStatus,
)
from .serializers import (
    ServiceAddonSerializer,
    ServiceBulkActionSerializer,
    ServiceCategoryCreateSerializer,
    ServiceCategoryDetailSerializer,
    ServiceCategoryListSerializer,
    ServiceCreateSerializer,
    ServiceDetailSerializer,
    ServiceImageSerializer,
    ServiceListSerializer,
    ServiceProviderCreateSerializer,
    ServiceProviderDetailSerializer,
)


class ServiceCategoryFilter(filters.FilterSet):
    """Filters for service categories."""
    
    name = filters.CharFilter(lookup_expr="icontains")
    parent = filters.UUIDFilter(field_name="parent_id")
    is_root = filters.BooleanFilter(method="filter_is_root")
    
    class Meta:
        model = ServiceCategory
        fields = ["name", "parent", "is_active"]
    
    def filter_is_root(self, queryset, name, value):
        if value:
            return queryset.filter(parent__isnull=True)
        return queryset.filter(parent__isnull=False)


@require_capability("services")
class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for service categories.
    
    Endpoints:
    - GET /categories/ - List categories
    - POST /categories/ - Create category (admin)
    - GET /categories/{id}/ - Get category details
    - PATCH /categories/{id}/ - Update category (admin)
    - DELETE /categories/{id}/ - Delete category (admin)
    """
    
    queryset = ServiceCategory.objects.all()
    filterset_class = ServiceCategoryFilter
    lookup_field = "id"
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == "list":
            return ServiceCategoryListSerializer
        if self.action == "retrieve":
            return ServiceCategoryDetailSerializer
        return ServiceCategoryCreateSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Non-admins only see active
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        
        return qs.select_related("parent").prefetch_related("subcategories")


class ServiceFilter(filters.FilterSet):
    """Filters for services."""
    
    name = filters.CharFilter(lookup_expr="icontains")
    category = filters.UUIDFilter(field_name="category_id")
    category_slug = filters.CharFilter(field_name="category__slug")
    status = filters.ChoiceFilter(choices=ServiceStatus.choices)
    pricing_type = filters.CharFilter()
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    min_duration = filters.NumberFilter(field_name="duration_minutes", lookup_expr="gte")
    max_duration = filters.NumberFilter(field_name="duration_minutes", lookup_expr="lte")
    requires_booking = filters.BooleanFilter()
    has_discount = filters.BooleanFilter(method="filter_has_discount")
    provider = filters.UUIDFilter(method="filter_by_provider")
    tag = filters.CharFilter(method="filter_by_tag")
    
    class Meta:
        model = Service
        fields = [
            "name",
            "category",
            "category_slug",
            "status",
            "pricing_type",
            "requires_booking",
        ]
    
    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(
                compare_price__isnull=False,
                compare_price__gt=models.F("price"),
            )
        return queryset.filter(
            Q(compare_price__isnull=True) | Q(compare_price__lte=models.F("price"))
        )
    
    def filter_by_provider(self, queryset, name, value):
        return queryset.filter(
            providers__user_id=value,
            providers__is_active=True,
        )
    
    def filter_by_tag(self, queryset, name, value):
        return queryset.filter(tags__contains=[value])


@require_capability("services")
class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD for services with provider management.
    
    Endpoints:
    - GET /services/ - List services
    - POST /services/ - Create service (admin)
    - GET /services/{id}/ - Get service details
    - PATCH /services/{id}/ - Update service (admin)
    - DELETE /services/{id}/ - Delete service (admin)
    - POST /services/{id}/providers/ - Add provider (admin)
    - DELETE /services/{id}/providers/{provider_id}/ - Remove provider (admin)
    - POST /services/{id}/images/ - Add image (admin)
    - DELETE /services/{id}/images/{image_id}/ - Remove image (admin)
    - POST /services/{id}/addons/ - Add addon (admin)
    - DELETE /services/{id}/addons/{addon_id}/ - Remove addon (admin)
    - POST /services/bulk/ - Bulk actions (admin)
    """
    
    queryset = Service.objects.all()
    filterset_class = ServiceFilter
    lookup_field = "id"
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == "list":
            return ServiceListSerializer
        if self.action == "retrieve":
            return ServiceDetailSerializer
        if self.action == "add_provider":
            return ServiceProviderCreateSerializer
        if self.action == "add_image":
            return ServiceImageSerializer
        if self.action == "add_addon":
            return ServiceAddonSerializer
        if self.action == "bulk_action":
            return ServiceBulkActionSerializer
        return ServiceCreateSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Non-admins only see active
        if not self.request.user.is_staff:
            qs = qs.filter(status=ServiceStatus.ACTIVE)
        
        if self.action == "list":
            return qs.select_related("category").annotate(
                provider_count=Count("providers", filter=Q(providers__is_active=True))
            )
        
        if self.action == "retrieve":
            return qs.select_related("category", "created_by").prefetch_related(
                "images",
                "addons",
                "providers__user",
            )
        
        return qs
    
    @action(detail=True, methods=["post"], url_path="providers")
    def add_provider(self, request, id=None):
        """Add a provider to the service."""
        service = self.get_object()
        serializer = ServiceProviderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check for existing assignment
        user_id = serializer.validated_data["user_id"]
        if ServiceProvider.objects.filter(service=service, user_id=user_id).exists():
            return Response(
                {"detail": "Provider already assigned to this service"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Create provider assignment
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        provider = ServiceProvider.objects.create(
            service=service,
            user=user,
            is_primary=serializer.validated_data.get("is_primary", False),
            is_active=serializer.validated_data.get("is_active", True),
            custom_price=serializer.validated_data.get("custom_price"),
            custom_duration=serializer.validated_data.get("custom_duration"),
            bio=serializer.validated_data.get("bio", ""),
        )
        
        return Response(
            ServiceProviderDetailSerializer(provider).data,
            status=status.HTTP_201_CREATED,
        )
    
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"providers/(?P<provider_id>[^/.]+)",
    )
    def remove_provider(self, request, id=None, provider_id=None):
        """Remove a provider from the service."""
        service = self.get_object()
        
        try:
            provider = ServiceProvider.objects.get(
                id=provider_id,
                service=service,
            )
            provider.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ServiceProvider.DoesNotExist:
            return Response(
                {"detail": "Provider not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(detail=True, methods=["post"], url_path="images")
    def add_image(self, request, id=None):
        """Add an image to the service."""
        service = self.get_object()
        serializer = ServiceImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        image = ServiceImage.objects.create(
            service=service,
            **serializer.validated_data,
        )
        
        return Response(
            ServiceImageSerializer(image).data,
            status=status.HTTP_201_CREATED,
        )
    
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_id>[^/.]+)",
    )
    def remove_image(self, request, id=None, image_id=None):
        """Remove an image from the service."""
        service = self.get_object()
        
        try:
            image = ServiceImage.objects.get(
                id=image_id,
                service=service,
            )
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ServiceImage.DoesNotExist:
            return Response(
                {"detail": "Image not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(detail=True, methods=["post"], url_path="addons")
    def add_addon(self, request, id=None):
        """Add an addon to the service."""
        service = self.get_object()
        serializer = ServiceAddonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        addon = ServiceAddon.objects.create(
            service=service,
            **serializer.validated_data,
        )
        
        return Response(
            ServiceAddonSerializer(addon).data,
            status=status.HTTP_201_CREATED,
        )
    
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"addons/(?P<addon_id>[^/.]+)",
    )
    def remove_addon(self, request, id=None, addon_id=None):
        """Remove an addon from the service."""
        service = self.get_object()
        
        try:
            addon = ServiceAddon.objects.get(
                id=addon_id,
                service=service,
            )
            addon.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ServiceAddon.DoesNotExist:
            return Response(
                {"detail": "Addon not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_action(self, request):
        """Perform bulk actions on services."""
        serializer = ServiceBulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service_ids = serializer.validated_data["service_ids"]
        action_type = serializer.validated_data["action"]
        
        services = Service.objects.filter(id__in=service_ids)
        
        if action_type == "activate":
            services.update(status=ServiceStatus.ACTIVE)
        elif action_type == "deactivate":
            services.update(status=ServiceStatus.INACTIVE)
        elif action_type == "archive":
            services.update(status=ServiceStatus.ARCHIVED)
        elif action_type == "delete":
            services.delete()
        
        return Response({
            "message": f"Successfully performed {action_type} on {len(service_ids)} services",
            "affected_count": len(service_ids),
        })
