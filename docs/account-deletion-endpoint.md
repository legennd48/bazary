# Account Self-Deletion Endpoint

## Overview
A secure endpoint that allows authenticated users to permanently delete their own accounts.

## Endpoint Details

**URL**: `/api/v1/auth/delete-account/`  
**Method**: `DELETE`  
**Authentication**: Required (JWT Token)

## Request Format

```json
{
  "password": "your_current_password",
  "confirmation_text": "DELETE MY ACCOUNT"
}
```

## Security Features

1. **Authentication Required**: User must be logged in with valid JWT token
2. **Password Verification**: Current password must be provided for security
3. **Confirmation Text**: Exact text "DELETE MY ACCOUNT" must be typed to confirm
4. **Irreversible Action**: Account deletion cannot be undone

## Data Cleanup

When an account is deleted, the following data is permanently removed:
- User profile and basic information
- User addresses
- User activity history
- Shopping cart and cart items
- Payment methods (tokens are invalidated)
- User preferences and settings

## Response Examples

### Success Response (200 OK)
```json
{
  "message": "User account deleted successfully",
  "detail": "Your account has been permanently deleted. We're sorry to see you go.",
  "deleted_user": "user@example.com"
}
```

### Validation Error (400 Bad Request)
```json
{
  "password": ["Incorrect password."],
  "confirmation_text": ["Please type 'DELETE MY ACCOUNT' to confirm account deletion."]
}
```

### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Usage Examples

### Using cURL
```bash
curl -X DELETE "http://localhost:8001/api/v1/auth/delete-account/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "your_current_password",
    "confirmation_text": "DELETE MY ACCOUNT"
  }'
```

### Using JavaScript/Axios
```javascript
const response = await axios.delete('/api/v1/auth/delete-account/', {
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  data: {
    password: 'your_current_password',
    confirmation_text: 'DELETE MY ACCOUNT'
  }
});
```

### Using Python requests
```python
import requests

response = requests.delete(
    'http://localhost:8001/api/v1/auth/delete-account/',
    headers={
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    },
    json={
        'password': 'your_current_password',
        'confirmation_text': 'DELETE MY ACCOUNT'
    }
)
```

## Frontend Integration Notes

### User Experience Considerations
1. **Warning Messages**: Display clear warnings about permanent deletion
2. **Confirmation Steps**: Implement multi-step confirmation process
3. **Password Input**: Use secure password input fields
4. **Logout After Deletion**: Automatically log out user after successful deletion
5. **Error Handling**: Provide clear error messages for validation failures

### Sample Frontend Flow
```javascript
// Step 1: Show warning modal
const showDeleteAccountWarning = () => {
  // Display modal with warnings about permanent deletion
  // List what data will be deleted
  // Require user to check "I understand" boxes
};

// Step 2: Password confirmation
const confirmDeletion = async (password) => {
  try {
    const response = await deleteAccount(password, 'DELETE MY ACCOUNT');
    
    if (response.status === 204) {
      // Account deleted successfully
      logout(); // Clear tokens and redirect to home
      showSuccessMessage('Account deleted successfully');
    }
  } catch (error) {
    if (error.response?.status === 400) {
      // Show validation errors
      showValidationErrors(error.response.data);
    } else {
      showErrorMessage('An error occurred during deletion');
    }
  }
};
```

## Testing

Run the tests for the account deletion endpoint:

```bash
# Run specific test file
python manage.py test apps.authentication.tests.test_account_deletion

# Run all authentication tests
python manage.py test apps.authentication
```

## Security Notes

- The endpoint logs account deletion attempts for security auditing
- User sessions are invalidated after successful deletion
- Related data is cleaned up through database CASCADE relationships
- Some business-critical data (like completed orders) may be preserved for legal requirements

## Alternative Actions

Before implementing account deletion, consider offering users alternatives:
- **Account Deactivation**: Temporarily disable account
- **Data Export**: Allow users to download their data first
- **Privacy Settings**: Enhanced privacy controls instead of deletion
- **Support Contact**: Direct users to support for complex cases