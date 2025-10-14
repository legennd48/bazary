"""
Test for account deletion endpoint.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AccountDeletionTestCase(TestCase):
    """Test cases for account self-deletion."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        
        # Create JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set up authenticated client
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.url = reverse('delete_account')
    
    def test_delete_account_requires_authentication(self):
        """Test that account deletion requires authentication."""
        # Remove authentication
        self.client.credentials()
        
        response = self.client.delete(self.url, {
            'password': 'testpassword123',
            'confirmation_text': 'DELETE MY ACCOUNT'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_account_requires_correct_password(self):
        """Test that account deletion requires correct password."""
        response = self.client.delete(self.url, {
            'password': 'wrongpassword',
            'confirmation_text': 'DELETE MY ACCOUNT'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_delete_account_requires_confirmation_text(self):
        """Test that account deletion requires exact confirmation text."""
        response = self.client.delete(self.url, {
            'password': 'testpassword123',
            'confirmation_text': 'DELETE MY ACCOUNT PLEASE'  # Wrong text
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmation_text', response.data)
    
    def test_successful_account_deletion(self):
        """Test successful account deletion."""
        # Verify user exists before deletion
        self.assertTrue(User.objects.filter(id=self.user.id).exists())
        
        response = self.client.delete(self.url, {
            'password': 'testpassword123',
            'confirmation_text': 'DELETE MY ACCOUNT'
        })
        
        # Should return 200 OK with success message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User account deleted successfully')
        self.assertIn('deleted_user', response.data)
        self.assertEqual(response.data['deleted_user'], self.user.email)
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
    
    def test_account_deletion_without_password_field(self):
        """Test account deletion without password field."""
        response = self.client.delete(self.url, {
            'confirmation_text': 'DELETE MY ACCOUNT'
            # Missing password field
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_account_deletion_without_confirmation_field(self):
        """Test account deletion without confirmation field."""
        response = self.client.delete(self.url, {
            'password': 'testpassword123'
            # Missing confirmation_text field
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirmation_text', response.data)