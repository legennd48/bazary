# Shopping Cart API Guide

This guide explains how to work with the shopping cart functionality in the Bazary E-Commerce API.

## 🛒 Adding Items to Cart - Complete Guide

There are **two ways** to add items to a cart in the Bazary API:

### Method 1: Add to Specific Cart (Recommended)
**Endpoint:** `POST /api/v1/payments/carts/{cart_id}/add_item/`

### Method 2: Add to Current Active Cart  
**Endpoint:** First get current cart, then use Method 1

---

## 📋 Step-by-Step Process

### Step 1: Get or Create a Cart
```bash
# Get your current active cart (creates one if none exists)
GET /api/v1/payments/carts/current/
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "currency": "USD",
  "total_amount": "0.00",
  "items": []
}
```

### Step 2: Add Items to Cart

**Endpoint:** `POST /api/v1/payments/carts/{cart_id}/add_item/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

---

## 🎯 Adding Different Types of Items

### Example 1: Add a Simple Product
```json
{
  "product_id": 1,
  "quantity": 2,
  "notes": "Gift wrapping required"
}
```

### Example 2: Add a Product Variant (e.g., specific size/color)
```json
{
  "product_id": 1,
  "variant_id": 5,
  "quantity": 1,
  "custom_attributes": {
    "size": "Large",
    "color": "Blue",
    "personalization": "Happy Birthday!"
  },
  "notes": "Rush delivery please"
}
```

### Example 3: Add Multiple Quantities
```json
{
  "product_id": 3,
  "quantity": 5,
  "custom_attributes": {
    "bulk_discount": "applied"
  }
}
```

---

## 📝 Request Fields Explained

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | integer | ✅ Required | ID of the product to add |
| `variant_id` | integer | ❌ Optional | ID of specific product variant (size, color, etc.) |
| `quantity` | integer | ❌ Optional | Number of items (default: 1, minimum: 1) |
| `custom_attributes` | object | ❌ Optional | Custom properties like size, color, personalization |
| `notes` | string | ❌ Optional | Special instructions (max 500 characters) |

---

## 🔄 How It Works Behind the Scenes

1. **Duplicate Detection**: If the same product/variant is already in cart, it **adds to existing quantity** instead of creating a duplicate item
2. **Stock Validation**: Automatically checks if enough stock is available
3. **Price Calculation**: Uses variant price if specified, otherwise uses base product price
4. **Inventory Updates**: Reserves inventory when items are added

---

## ✅ Success Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "currency": "USD",
  "total_amount": "129.98",
  "tax_amount": "10.40",
  "items": [
    {
      "id": "item-uuid",
      "product_name": "Wireless Headphones",
      "variant_name": "Blue - Large",
      "quantity": 2,
      "unit_price": "59.99",
      "total_price": "119.98",
      "custom_attributes": {
        "size": "Large",
        "color": "Blue"
      },
      "notes": "Gift wrapping required"
    }
  ]
}
```

---

## 🚨 Error Responses

### Product Not Found (400)
```json
{
  "non_field_errors": ["Product not found or inactive."]
}
```

### Insufficient Stock (400)
```json
{
  "non_field_errors": ["Not enough stock available for product."]
}
```

### Invalid Variant (400)
```json
{
  "non_field_errors": ["Product variant not found or inactive."]
}
```

---

## 🛠️ Complete Cart Management Operations

### View Cart Contents
```bash
GET /api/v1/payments/carts/{cart_id}/
Authorization: Bearer <your_jwt_token>
```

### Get Cart Summary
```bash
GET /api/v1/payments/carts/{cart_id}/summary/
Authorization: Bearer <your_jwt_token>
```

### Update Cart Item
```bash
PATCH /api/v1/payments/carts/{cart_id}/items/{item_id}/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "quantity": 3,
  "notes": "Updated instructions"
}
```

### Remove Item from Cart
```bash
DELETE /api/v1/payments/carts/{cart_id}/items/{item_id}/
Authorization: Bearer <your_jwt_token>
```

### Clear Entire Cart
```bash
POST /api/v1/payments/carts/{cart_id}/clear/
Authorization: Bearer <your_jwt_token>
```

---

## 🧪 Full cURL Examples

### Complete Workflow Example
```bash
# 1. Get current cart
curl -X GET "http://localhost:8000/api/v1/payments/carts/current/" \
  -H "Authorization: Bearer your_jwt_token_here"

# 2. Add item to cart (use cart ID from step 1)
curl -X POST "http://localhost:8000/api/v1/payments/carts/your-cart-id/add_item/" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "variant_id": 5,
    "quantity": 2,
    "custom_attributes": {
      "size": "Large",
      "color": "Blue"
    },
    "notes": "Gift wrapping required"
  }'

# 3. View updated cart
curl -X GET "http://localhost:8000/api/v1/payments/carts/your-cart-id/" \
  -H "Authorization: Bearer your_jwt_token_here"

# 4. Update item quantity
curl -X PATCH "http://localhost:8000/api/v1/payments/carts/your-cart-id/items/item-id/" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 3
  }'

# 5. Get cart summary
curl -X GET "http://localhost:8000/api/v1/payments/carts/your-cart-id/summary/" \
  -H "Authorization: Bearer your_jwt_token_here"
```

---

## 🔐 Authentication Requirements

All cart operations require JWT authentication:

1. **Get JWT Token**: Use the login endpoint to get your access token
   ```bash
   POST /api/v1/auth/token/
   {
     "email": "your-email@example.com",
     "password": "your-password"
   }
   ```

2. **Use Token**: Include the token in all cart requests
   ```
   Authorization: Bearer your_access_token_here
   ```

---

## 💡 Pro Tips & Best Practices

### 🎯 Cart Management Tips
1. **Always get current cart first** - This ensures you're working with the user's active cart
2. **Use variants for customization** - Different sizes, colors, etc. should use `variant_id`
3. **Batch operations** - Add multiple different products with separate API calls
4. **Check stock first** - The API validates stock, but you can check product stock beforehand
5. **Custom attributes** - Use for any special customization that doesn't warrant a full variant

### 🔄 Workflow Best Practices
1. **Session Management**: Each user should have one active cart at a time
2. **Stock Validation**: The API automatically validates stock, but consider showing availability on the frontend
3. **Price Updates**: Cart totals are calculated automatically based on current product prices
4. **Error Handling**: Always handle stock shortage and product availability errors gracefully

### 🛡️ Security Considerations
1. **User Isolation**: Users can only access their own carts (enforced by JWT authentication)
2. **Stock Protection**: Inventory is validated on every cart operation
3. **Price Integrity**: Prices are always fetched from the current product/variant data

---

## 🔗 Related Endpoints

- **Products**: `/api/v1/products/products/` - Browse available products
- **Product Variants**: `/api/v1/products/variants/` - View product variants
- **Payment Processing**: `/api/v1/payments/transactions/initiate/` - Process cart payment
- **User Profile**: `/api/v1/auth/profile/` - Manage user account

---

## 📖 Additional Resources

- **API Documentation**: Available at `/api/schema/swagger-ui/`
- **Authentication Guide**: See authentication documentation
- **Payment Processing**: See payment integration guide
- **Product Management**: See product management documentation

The cart system automatically handles inventory management, price calculations, and duplicate prevention for you! 🎉
