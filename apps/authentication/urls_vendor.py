"""
Vendor URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.authentication.views.vendor import (
    VendorRegistrationView,
    VendorProfileView,
    VendorDocumentViewSet,
    VendorDashboardView,
    VendorPublicViewSet,
    AdminVendorListView,
    AdminVendorDetailView,
    AdminVendorApplicationsView,
)

app_name = 'vendors'

router = DefaultRouter()
router.register(r'documents', VendorDocumentViewSet, basename='vendor-documents')
router.register(r'stores', VendorPublicViewSet, basename='vendor-stores')

urlpatterns = [
    # Public endpoints
    path('', include(router.urls)),

    # Vendor registration
    path('register/', VendorRegistrationView.as_view(), name='register'),

    # Vendor self-service
    path('profile/', VendorProfileView.as_view(), name='profile'),
    path('dashboard/', VendorDashboardView.as_view(), name='dashboard'),

    # Admin endpoints
    path('admin/list/', AdminVendorListView.as_view(), name='admin-list'),
    path('admin/applications/', AdminVendorApplicationsView.as_view(), name='admin-applications'),
    path('admin/<uuid:vendor_id>/', AdminVendorDetailView.as_view(), name='admin-detail'),
]
