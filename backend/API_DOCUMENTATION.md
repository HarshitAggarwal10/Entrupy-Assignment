# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

The API supports API key authentication via the `X-API-Key` header. All requests are logged automatically.

### Create API Key
```bash
POST /api/api-keys?name=YourAppName
```

Response:
```json
{
  "name": "YourAppName",
  "api_key": "550e8400-e29b-41d4-a716-446655440000",
  "message": "API key created. Use this key in X-API-Key header.",
  "warning": "Save this key securely. You won't be able to see it again."
}
```

### Using API Key in Requests
```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:8000/api/products
```

---

## Endpoints

### 1. Data Management

#### Refresh Data from Sample Products
```bash
POST /api/data/refresh
```

Response:
```json
{
  "message": "Data refresh completed",
  "imported_count": 0,
  "updated_count": 90,
  "error_count": 0,
  "new_price_changes": 0,
  "duration_seconds": 2.5
}
```

---

### 2. Browse & Filter Products

#### Get All Products (with filtering)
```bash
GET /api/products?brand=Chanel&source=1stdibs&min_price=100&max_price=5000&skip=0&limit=50&sort_by=price&sort_order=desc
```

Query Parameters:
- `brand` (optional) - Filter by brand name
- `category` (optional) - Filter by category
- `source` (optional) - Filter by marketplace (1stdibs, fashionphile, grailed)
- `min_price` (optional) - Minimum price threshold
- `max_price` (optional) - Maximum price threshold
- `skip` (optional, default=0) - Pagination offset
- `limit` (optional, default=50) - Number of results (max=100)
- `sort_by` (optional, default=created_at) - Sort field (price or created_at)
- `sort_order` (optional, default=desc) - Sort order (asc or desc)

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Product Name",
      "brand": "Brand Name",
      "price": 1500.00,
      "source": "1stdibs",
      "category": "Accessories",
      "condition": "Good",
      "size": "Medium",
      "product_url": "https://...",
      "image_url": "https://...",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 90,
  "skip": 0,
  "limit": 50
}
```

---

### 3. Product Details

#### Get Single Product with Price History
```bash
GET /api/products/{product_id}
```

Response:
```json
{
  "id": "uuid",
  "title": "Product Name",
  "brand": "Brand Name",
  "price": 1500.00,
  "source": "1stdibs",
  "category": "Accessories",
  "condition": "Good",
  "size": "Medium",
  "product_url": "https://...",
  "image_url": "https://...",
  "price_history": [
    {
      "id": "uuid",
      "price": 1500.00,
      "currency": "USD",
      "recorded_at": "2024-01-01T12:00:00Z"
    }
  ],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Get Price History for Product
```bash
GET /api/products/{product_id}/price-history?limit=50
```

Response:
```json
[
  {
    "id": "uuid",
    "product_id": "uuid",
    "price": 1500.00,
    "currency": "USD",
    "recorded_at": "2024-01-01T12:00:00Z"
  }
]
```

---

### 4. Analytics & Aggregates

#### Get Aggregate Analytics
```bash
GET /api/analytics
```

Response:
```json
{
  "total_products": 90,
  "products_by_source": {
    "1stdibs": 30,
    "fashionphile": 30,
    "grailed": 30
  },
  "products_by_category": {
    "Accessories": 45,
    "Apparel": 45
  },
  "products_by_brand": {
    "Chanel": 30,
    "Tiffany": 30,
    "Amiri": 30
  },
  "price_statistics": {
    "min_price": 50.00,
    "max_price": 5000.00,
    "avg_price": 1250.00
  },
  "average_prices_by_source": {
    "1stdibs": 1300.00,
    "fashionphile": 1250.00,
    "grailed": 1200.00
  },
  "average_prices_by_category": {
    "Accessories": 1400.00,
    "Apparel": 1100.00
  }
}
```

#### Get System Statistics
```bash
GET /api/stats
```

---

### 5. Notifications

#### Get Notification Events
```bash
GET /api/notifications?is_processed=false&skip=0&limit=50
```

Query Parameters:
- `is_processed` (optional) - Filter by processed status (true/false)
- `skip` (optional, default=0) - Pagination offset
- `limit` (optional, default=50) - Number of results (max=100)

Response:
```json
{
  "data": [
    {
      "id": "uuid",
      "product_id": "uuid",
      "old_price": 1500.00,
      "new_price": 1450.00,
      "percentage_change": -3.33,
      "event_type": "price_decrease",
      "processed": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

#### Process Pending Notifications
```bash
POST /api/notifications/process
```

Response:
```json
{
  "message": "Notifications processed",
  "processed_count": 5,
  "remaining_count": 0
}
```

---

### 6. API Key Management

#### List All API Keys
```bash
GET /api/api-keys
```

Response:
```json
{
  "total": 2,
  "keys": [
    {
      "id": "uuid",
      "name": "Mobile App",
      "created_at": "2024-01-01T12:00:00Z",
      "last_used": "2024-01-02T10:30:00Z",
      "key": "550e8400...0000"
    }
  ]
}
```

#### Get API Key Usage
```bash
GET /api/api-keys/{key_id}/usage
```

Response:
```json
{
  "total_requests": 150,
  "requests": [
    {
      "method": "GET",
      "path": "/api/products",
      "status": 200,
      "response_time_ms": 45.5,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Revoke API Key
```bash
POST /api/api-keys/{key_id}/revoke
```

Response:
```json
{
  "message": "API key 'Mobile App' has been revoked"
}
```

---

### 7. Request Logs

#### Get Request Logs
```bash
GET /api/request-logs?api_key_id=optional&skip=0&limit=100
```

Query Parameters:
- `api_key_id` (optional) - Filter by API key
- `skip` (optional, default=0) - Pagination offset
- `limit` (optional, default=100) - Number of results (max=500)

Response:
```json
{
  "total": 500,
  "skip": 0,
  "limit": 100,
  "logs": [
    {
      "method": "GET",
      "path": "/api/products",
      "status_code": 200,
      "response_time_ms": 45.5,
      "timestamp": "2024-01-01T12:00:00Z",
      "api_key_id": "uuid or null"
    }
  ]
}
```

---

### 8. System

#### Health Check
```bash
GET /api/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `500` - Server Error

Error Response Format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Example Usage

### Complete Workflow

1. **Create API Key**
   ```bash
   curl -X POST "http://localhost:8000/api/api-keys?name=MyApp"
   ```

2. **Use API Key in Requests**
   ```bash
   curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/products"
   ```

3. **Filter Products**
   ```bash
   curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/products?brand=Chanel&min_price=500&max_price=2000"
   ```

4. **View Product Details**
   ```bash
   curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/products/product-id"
   ```

5. **Get Analytics**
   ```bash
   curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/analytics"
   ```

6. **Check Usage**
   ```bash
   curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/api-keys/key-id/usage"
   ```

---

## Rate Limiting

Currently, the API does not enforce rate limiting. This can be added based on API key usage statistics.

---

## Swagger Documentation

Interactive API documentation available at:
```
http://localhost:8000/docs
```
