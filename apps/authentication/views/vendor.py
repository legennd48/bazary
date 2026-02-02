"""
Vendor views for multi-vendor marketplace.
"""

from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import Vendor, VendorDocument, VendorApplication
from apps.authentication.serializers.vendor import (
    VendorSerializer,
    VendorPublicSerializer,
    VendorDocumentSerializer,
    VendorApplicationSerializer,
    VendorRegistrationSerializer,
    AdminVendorVerificationSerializer,
)


class IsVendor(permissions.BasePermission):
    """Permission check for vendor access."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'vendor_profile')
        )


class IsAdminUser(permissions.BasePermission):
    """Permission check for admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('admin')


class VendorRegistrationView(APIView):
    """
    Register as a vendor.

    POST: Submit vendor registration application
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VendorRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()

        return Response({
            'message': 'Vendor registration submitted successfully. Your application is under review.',
            'vendor': VendorSerializer(vendor).data,
        }, status=status.HTTP_201_CREATED)


class VendorProfileView(APIView):
    """
    Manage vendor profile.

    GET: Get current vendor's profile
    PATCH: Update vendor profile
    """
    permission_classes = [IsVendor]

    def get(self, request):
        vendor = request.user.vendor_profile
        return Response(VendorSerializer(vendor).data)

    def patch(self, request):
        vendor = request.user.vendor_profile
        serializer = VendorSerializer(vendor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VendorDocumentViewSet(viewsets.ModelViewSet):
    """
    Manage vendor documents.
    """
    serializer_class = VendorDocumentSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return VendorDocument.objects.filter(vendor=self.request.user.vendor_profile)

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user.vendor_profile)


class VendorDashboardView(APIView):
    """
    Vendor dashboard with statistics.
    """
    permission_classes = [IsVendor]

    def get(self, request):
        vendor = request.user.vendor_profile

        # Get recent orders for this vendor (when products have vendor FK)
        # For now, return basic vendor stats

        return Response({
            'vendor': VendorSerializer(vendor).data,
            'stats': {
                'total_products': vendor.total_products,
                'total_orders': vendor.total_orders,
                'total_revenue': str(vendor.total_revenue),
                'average_rating': str(vendor.average_rating),
                'total_reviews': vendor.total_reviews,
            },
            'verification': {
                'status': vendor.verification_status,
                'is_verified': vendor.is_verified,
                'can_sell': vendor.can_sell,
            },
        })


class VendorPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public vendor store listings.
    """
    serializer_class = VendorPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Vendor.objects.filter(is_active=True, verification_status='verified')

    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products from this vendor."""
        vendor = self.get_object()
        # When products have vendor FK, filter by vendor
        # For now, return empty list
        return Response({
            'vendor': VendorPublicSerializer(vendor).data,
            'products': [],
            'message': 'Products endpoint - will be populated when Product.vendor relationship is added'
        })


# Admin Views

class AdminVendorListView(APIView):
    """
    Admin: List all vendors with filtering.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status', None)
        queryset = Vendor.objects.all().order_by('-created_at')

        if status_filter:
            queryset = queryset.filter(verification_status=status_filter)

        vendors = VendorSerializer(queryset, many=True).data
        return Response({
            'count': queryset.count(),
            'results': vendors,
        })


class AdminVendorDetailView(APIView):
    """
    Admin: Manage individual vendor.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, vendor_id):
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(VendorSerializer(vendor).data)

    def post(self, request, vendor_id):
        """Handle verification actions."""
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminVendorVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')

        if action == 'approve':
            vendor.verification_status = 'verified'
            vendor.is_active = True
            vendor.verified_at = timezone.now()
            vendor.verified_by = request.user
            vendor.verification_notes = notes
            vendor.save()

            # Update related application
            if hasattr(vendor, 'application'):
                vendor.application.status = 'approved'
                vendor.application.reviewed_by = request.user
                vendor.application.reviewed_at = timezone.now()
                vendor.application.save()

            message = 'Vendor approved and activated successfully.'

        elif action == 'reject':
            vendor.verification_status = 'rejected'
            vendor.is_active = False
            vendor.verification_notes = serializer.validated_data.get('rejection_reason', '')
            vendor.save()

            if hasattr(vendor, 'application'):
                vendor.application.status = 'rejected'
                vendor.application.rejection_reason = serializer.validated_data.get('rejection_reason', '')
                vendor.application.reviewed_by = request.user
                vendor.application.reviewed_at = timezone.now()
                vendor.application.save()

            message = 'Vendor application rejected.'

        elif action == 'request_documents':
            vendor.verification_status = 'documents_required'
            vendor.verification_notes = notes
            vendor.save()
            message = 'Requested additional documents from vendor.'

        elif action == 'suspend':
            vendor.verification_status = 'suspended'
            vendor.is_active = False
            vendor.verification_notes = notes
            vendor.save()
            message = 'Vendor has been suspended.'

        return Response({
            'message': message,
            'vendor': VendorSerializer(vendor).data,
        })


class AdminVendorApplicationsView(APIView):
    """
    Admin: List pending vendor applications.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status', 'submitted')
        queryset = VendorApplication.objects.filter(status=status_filter).order_by('-created_at')

        applications = VendorApplicationSerializer(queryset, many=True).data
        return Response({
            'count': queryset.count(),
            'results': applications,
        })
