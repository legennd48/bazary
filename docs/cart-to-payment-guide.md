# 🛒 Cart to Payment Process Guide

Complete step-by-step guide for adding products to cart and processing payments through the Bazary API.

## 📋 Prerequisites

- User account created and authenticated
- Valid JWT token obtained from `/api/v1/auth/login/`
- At least one product available in the system
- Payment provider configured (Chapa for ETB payments)

## 🔄 Complete Workflow

### Step 1: Authentication

First, obtain your JWT token by logging in:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Use the `access` token in all subsequent requests as: `Authorization: Bearer <access_token>`

### Step 2: Browse Products

Get available products to add to cart:

```bash
curl -X GET http://127.0.0.1:8000/api/v1/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 50,
  "next": "http://127.0.0.1:8000/api/v1/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Smartphone XYZ",
      "description": "Latest smartphone with amazing features",
      "price": "999.99",
      "currency": "ETB",
      "category": {
        "id": 2,
        "name": "Electronics"
      },
      "stock_quantity": 50,
      "is_in_stock": true,
      "sku": "PHONE-XYZ-001"
    }
  ]
}
```

### Step 3: Get or Create Cart

Get your current active cart (creates one if none exists):

```bash
curl -X GET http://127.0.0.1:8000/api/v1/payments/carts/current/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "id": "97d58653-ca7a-4c70-b259-7fca7b5fd1e5",
  "user_email": "user@example.com",
  "status": "active",
  "currency": "USD",
  "subtotal": "0.00",
  "tax_amount": "0.00",
  "shipping_amount": "0.00",
  "discount_amount": "0.00",
  "total": "0.00",
  "item_count": 0,
  "is_empty": true,
  "items": [],
  "created_at": "2025-08-09T10:00:00Z"
}
```

### Step 4: Add Products to Cart

Add items to your cart using the cart ID from step 3:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/add_item/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "notes": "Gift wrapping required"
  }'
```

**For products with variants:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/add_item/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "variant_id": 5,
    "quantity": 1,
    "custom_attributes": {
      "size": "Large",
      "color": "Blue"
    },
    "notes": "Express delivery"
  }'
```

**Response:**
```json
{
  "id": "97d58653-ca7a-4c70-b259-7fca7b5fd1e5",
  "user_email": "user@example.com",
  "status": "active",
  "currency": "USD",
  "subtotal": "1999.98",
  "tax_amount": "199.99",
  "shipping_amount": "50.00",
  "total": "2249.97",
  "item_count": 2,
  "is_empty": false,
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Smartphone XYZ",
        "price": "999.99"
      },
      "quantity": 2,
      "unit_price": "999.99",
      "total_price": "1999.98",
      "notes": "Gift wrapping required"
    }
  ]
}
```

### Step 5: Review Cart

Get cart summary before proceeding to payment:

```bash
curl -X GET http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/summary/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Step 6: Get Payment Providers

Check available payment providers:

```bash
curl -X GET http://127.0.0.1:8000/api/v1/payments/providers/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Chapa",
    "provider_type": "chapa",
    "is_active": true,
    "supported_currencies": ["ETB"],
    "test_mode": true
  }
]
```

### Step 7: Initiate Payment

Start the payment process using cart total:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/transactions/initiate/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": 1,
    "cart_id": "97d58653-ca7a-4c70-b259-7fca7b5fd1e5",
    "currency": "ETB",
    "description": "Purchase from cart",
    "reference": "ORDER-2025-001"
  }'
```

**Or initiate with specific amount:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/transactions/initiate/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": 1,
    "amount": "2249.97",
    "currency": "ETB",
    "description": "Purchase from cart",
    "reference": "ORDER-2025-001",
    "metadata": {
      "cart_id": "97d58653-ca7a-4c70-b259-7fca7b5fd1e5",
      "order_type": "cart_purchase"
    }
  }'
```

**Response:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "checkout_url": "https://checkout.chapa.co/checkout/payment/550e8400-e29b-41d4-a716-446655440000",
  "provider": "chapa",
  "message": "Payment initialized successfully"
}
```

### Step 8: Complete Payment

1. **Redirect user to checkout URL** from step 7 response
2. **User completes payment** on Chapa's secure checkout page
3. **User is redirected back** to your return URL
4. **Webhook notification** is sent to your callback URL

### Step 9: Verify Payment

After payment completion, verify the transaction status:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/transactions/verify/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tx_ref": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "succeeded",
  "amount": "2249.97",
  "currency": "ETB",
  "description": "Purchase from cart",
  "reference": "ORDER-2025-001",
  "processed_at": "2025-08-09T10:15:00Z",
  "provider_fee": "67.50",
  "is_refundable": true
}
```

### Step 10: Check Transaction Status

Get detailed transaction information:

```bash
curl -X GET http://127.0.0.1:8000/api/v1/payments/transactions/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛠️ Cart Management Operations

### Update Item Quantity

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/items/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 3
  }'
```

### Remove Item from Cart

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/items/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Clear Entire Cart

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/carts/97d58653-ca7a-4c70-b259-7fca7b5fd1e5/clear/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 💳 Payment Method Management (Optional)

### Save Payment Method

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/methods/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": 1,
    "method_type": "card",
    "name": "Personal Visa Card",
    "is_default": true,
    "provider_token": "pm_1234567890abcdef"
  }'
```

### Use Saved Payment Method

```bash
curl -X POST http://127.0.0.1:8000/api/v1/payments/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": 1,
    "provider": 1,
    "amount": "2249.97",
    "currency": "ETB",
    "description": "Purchase with saved method",
    "reference": "ORDER-2025-002"
  }'
```

## 🔍 Error Handling

### Common Error Responses

**Insufficient Stock:**
```json
{
  "error": "Not enough stock available. Only 5 units remaining."
}
```

**Invalid Product:**
```json
{
  "error": "Product not found or inactive."
}
```

**Payment Failed:**
```json
{
  "error": "Payment processing failed",
  "error_code": "insufficient_funds"
}
```

**Authentication Required:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## 📊 Status Codes

- **200**: Success - Operation completed
- **201**: Created - Resource created successfully
- **400**: Bad Request - Invalid data provided
- **401**: Unauthorized - Authentication required
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource doesn't exist
- **500**: Server Error - Internal server error

## 🎯 Best Practices

1. **Always validate stock** before adding items to cart
2. **Check cart totals** before initiating payment
3. **Handle webhook notifications** for real-time status updates
4. **Verify payments** after user returns from checkout
5. **Implement retry logic** for failed payment verifications
6. **Store transaction references** for order tracking
7. **Clear cart** after successful payment completion

## 🔗 Related Documentation

- [Shopping Cart Guide](./shopping-cart-guide.md)
- [Payment Integration Guide](./payment-integration-guide.md)
- [API Authentication](./authentication-guide.md)
- [Webhook Handling](./webhook-guide.md)

## 🐛 Troubleshooting

### Cart Issues
- Ensure user is authenticated
- Check product availability and stock
- Verify cart permissions

### Payment Issues
- Confirm provider is active
- Check currency compatibility
- Validate amount format
- Review webhook configuration

### Common Fixes
- Clear browser cache for frontend issues
- Check server logs for detailed error messages
- Verify API endpoint URLs are correct
- Ensure proper content-type headers
