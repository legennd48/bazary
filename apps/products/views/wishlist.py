"""
Wishlist API Views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.products.models import Wishlist, WishlistItem, Product
from apps.products.serializers.wishlist import (
    WishlistSerializer,
    WishlistSummarySerializer,
    WishlistItemSerializer,
    AddToWishlistSerializer,
    MoveWishlistItemSerializer,
)


class WishlistViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing user wishlists.
    
    Endpoints:
    - GET /wishlists/ - List user's wishlists
    - POST /wishlists/ - Create new wishlist
    - GET /wishlists/{id}/ - Get wishlist details with items
    - PUT/PATCH /wishlists/{id}/ - Update wishlist
    - DELETE /wishlists/{id}/ - Delete wishlist
    - POST /wishlists/add-item/ - Add item to wishlist
    - DELETE /wishlists/remove-item/{item_id}/ - Remove item
    - POST /wishlists/move-item/ - Move item between wishlists
    - GET /wishlists/shared/{token}/ - View shared wishlist
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == "list":
            return WishlistSummarySerializer
        if self.action == "add_item":
            return AddToWishlistSerializer
        if self.action == "move_item":
            return MoveWishlistItemSerializer
        return WishlistSerializer
    
    def get_queryset(self):
        """Return wishlists for current user."""
        return Wishlist.objects.filter(
            user=self.request.user
        ).prefetch_related("items__product__images")
    
    def perform_create(self, serializer):
        """Create wishlist for current user."""
        # Check if this should be the default
        is_first = not Wishlist.objects.filter(user=self.request.user).exists()
        serializer.save(
            user=self.request.user,
            is_default=is_first or serializer.validated_data.get("is_default", False),
        )
    
    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """
        Add item to wishlist.
        
        If no wishlist_id provided, adds to default wishlist (creates one if needed).
        """
        serializer = AddToWishlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wishlist_id = serializer.validated_data.get("wishlist_id")
        product_id = serializer.validated_data["product_id"]
        variant_id = serializer.validated_data.get("variant_id")
        notes = serializer.validated_data.get("notes", "")
        
        # Get or create wishlist
        if wishlist_id:
            wishlist = get_object_or_404(
                Wishlist,
                id=wishlist_id,
                user=request.user,
            )
        else:
            wishlist, created = Wishlist.objects.get_or_create(
                user=request.user,
                is_default=True,
                defaults={"name": "My Wishlist"},
            )
        
        # Check if item already exists
        existing = WishlistItem.objects.filter(
            wishlist=wishlist,
            product_id=product_id,
            variant_id=variant_id,
        ).first()
        
        if existing:
            return Response(
                {
                    "message": "Item already in wishlist",
                    "item": WishlistItemSerializer(existing, context={"request": request}).data,
                },
                status=status.HTTP_200_OK,
            )
        
        # Create new item
        product = Product.objects.get(id=product_id)
        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product,
            variant_id=variant_id,
            notes=notes,
        )
        
        return Response(
            {
                "message": "Item added to wishlist",
                "item": WishlistItemSerializer(item, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=False, methods=["delete"], url_path=r"remove-item/(?P<item_id>[^/.]+)")
    def remove_item(self, request, item_id=None):
        """Remove item from wishlist."""
        item = get_object_or_404(
            WishlistItem,
            id=item_id,
            wishlist__user=request.user,
        )
        item.delete()
        
        return Response(
            {"message": "Item removed from wishlist"},
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["post"])
    def move_item(self, request):
        """Move item between wishlists."""
        serializer = MoveWishlistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item = get_object_or_404(
            WishlistItem,
            id=serializer.validated_data["item_id"],
            wishlist__user=request.user,
        )
        
        target_wishlist = get_object_or_404(
            Wishlist,
            id=serializer.validated_data["target_wishlist_id"],
            user=request.user,
        )
        
        # Check if item already in target
        if WishlistItem.objects.filter(
            wishlist=target_wishlist,
            product=item.product,
            variant_id=item.variant_id,
        ).exists():
            return Response(
                {"error": "Item already exists in target wishlist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        item.wishlist = target_wishlist
        item.save()
        
        return Response(
            {
                "message": "Item moved successfully",
                "item": WishlistItemSerializer(item, context={"request": request}).data,
            },
            status=status.HTTP_200_OK,
        )
    
    @action(
        detail=False,
        methods=["get"],
        url_path=r"shared/(?P<token>[^/.]+)",
        permission_classes=[AllowAny],
    )
    def shared(self, request, token=None):
        """View a shared wishlist."""
        wishlist = get_object_or_404(
            Wishlist,
            share_token=token,
            is_public=True,
        )
        
        serializer = WishlistSerializer(wishlist, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def default(self, request):
        """Get user's default wishlist."""
        wishlist = Wishlist.objects.filter(
            user=request.user,
            is_default=True,
        ).first()
        
        if not wishlist:
            wishlist = Wishlist.objects.create(
                user=request.user,
                name="My Wishlist",
                is_default=True,
            )
        
        serializer = WishlistSerializer(wishlist, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def check(self, request):
        """
        Check if products are in any wishlist.
        
        Query params:
        - product_ids: comma-separated product IDs
        """
        product_ids = request.query_params.get("product_ids", "")
        if not product_ids:
            return Response({"in_wishlist": {}})
        
        product_id_list = [pid.strip() for pid in product_ids.split(",")]
        
        wishlist_items = WishlistItem.objects.filter(
            wishlist__user=request.user,
            product_id__in=product_id_list,
        ).values_list("product_id", flat=True)
        
        result = {
            str(pid): str(pid) in [str(x) for x in wishlist_items]
            for pid in product_id_list
        }
        
        return Response({"in_wishlist": result})
