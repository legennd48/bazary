"""
Account deletion view for self-service account deletion.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.swagger_docs import SwaggerTags
from ..serializers import AccountDeletionSerializer
from ..utils import log_user_activity

User = get_user_model()


class AccountDeletionView(APIView):
    """
    ## Account Self-Deletion
    
    Allows users to permanently delete their own account.
    
    ### 🚨 Important Warning
    - **This action is IRREVERSIBLE**
    - All user data will be permanently deleted
    - Associated orders, reviews, and preferences will be removed
    - Account cannot be recovered after deletion
    
    ### 🔐 Security Requirements
    - User must be authenticated
    - Current password confirmation required
    - Confirmation text must be typed exactly
    - All associated data is properly cleaned up
    
    ### 📋 Data Cleanup
    The following data is permanently deleted:
    - User account and profile
    - User addresses
    - User activities and history
    - Cart items
    - Payment methods (tokens invalidated)
    - Reviews and ratings
    - Saved preferences
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="🗑️ Delete User Account (Self)",
        operation_description="""
        ## ⚠️ PERMANENT Account Deletion
        
        This endpoint allows authenticated users to permanently delete their own account.
        
        ### 🔒 Security Requirements:
        1. **Authentication**: Must be logged in with valid JWT token
        2. **Password Confirmation**: Must provide current account password
        3. **Confirmation Text**: Must type exactly 'DELETE MY ACCOUNT'
        
        ### 🗑️ Data Removal Process:
        - **User Profile**: Permanently deleted
        - **User Addresses**: All addresses removed
        - **Shopping Cart**: Cart and items cleared
        - **Payment Methods**: All saved payment methods removed
        - **User Activities**: Activity history cleared
        - **Reviews**: All product reviews removed
        - **Preferences**: All user preferences cleared
        
        ### ⚠️ Important Notes:
        - **IRREVERSIBLE ACTION**: Account cannot be recovered
        - **Immediate Effect**: User will be logged out after deletion
        - **Related Orders**: Order history may be preserved for legal/business requirements
        - **Anonymous Data**: Some aggregated/anonymized data may be retained
        
        ### 🧪 Testing:
        ```bash
        # Test account deletion
        curl -X DELETE "http://localhost:8001/api/v1/auth/delete-account/" \\
          -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
          -H "Content-Type: application/json" \\
          -d '{
            "password": "your_current_password",
            "confirmation_text": "DELETE MY ACCOUNT"
          }'
        ```
        
        ### 🔄 Alternative Actions:
        If you're not sure about permanent deletion, consider:
        - **Account Deactivation**: Contact support to temporarily disable account
        - **Data Export**: Request your data before deletion
        - **Privacy Settings**: Adjust privacy settings instead of deletion
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["password", "confirmation_text"],
            properties={
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Current account password for security verification",
                    example="your_current_password"
                ),
                "confirmation_text": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Must type exactly: 'DELETE MY ACCOUNT'",
                    example="DELETE MY ACCOUNT"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Account deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="User account deleted successfully"
                        ),
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Your account has been permanently deleted. We're sorry to see you go."
                        ),
                        "deleted_user": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="user@example.com"
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "password": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Incorrect password."]
                        ),
                        "confirmation_text": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Please type 'DELETE MY ACCOUNT' to confirm account deletion."]
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="Unauthorized - Valid JWT token required",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Authentication credentials were not provided."
                        ),
                    },
                ),
            ),
        },
    )
    def delete(self, request):
        """Delete the authenticated user's account permanently."""
        serializer = AccountDeletionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            
            # Log the account deletion attempt
            log_user_activity(
                user=user,
                action="account_deletion_attempt",
                description="User initiated account deletion process"
            )
            
            # Perform the deletion within a transaction
            with transaction.atomic():
                try:
                    # Log final activity
                    log_user_activity(
                        user=user,
                        action="account_deleted",
                        description="User account permanently deleted by user request"
                    )
                    
                    # Store user info for response (before deletion)
                    user_email = user.email
                    
                    # Delete the user account (CASCADE will handle related objects)
                    user.delete()
                    
                    # Return success response
                    return Response(
                        {
                            "message": "User account deleted successfully",
                            "detail": "Your account has been permanently deleted. We're sorry to see you go.",
                            "deleted_user": user_email
                        },
                        status=status.HTTP_200_OK
                    )
                    
                except Exception as e:
                    # Log the error but don't expose internal details
                    return Response(
                        {
                            "error": "An error occurred during account deletion. Please try again or contact support.",
                            "detail": "Account deletion process failed"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)