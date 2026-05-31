# API Documentation

## Authentication

All endpoints (except the health check) require JWT authentication.

### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "pass"}'
```

### Use Token
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/core/settings/
```

## Core Endpoints

### Health Check
Exposed both at `/health/` and `/api/v1/core/health/`.
```
GET /health/
```
Returns:
```json
{
  "status": "healthy",
  "message": "API is running",
  "version": "1.0.0"
}
```

### API Logs
Used to track and monitor API requests and responses.
```
GET /api/v1/core/logs/
POST /api/v1/core/logs/
GET /api/v1/core/logs/{id}/
PUT /api/v1/core/logs/{id}/
PATCH /api/v1/core/logs/{id}/
DELETE /api/v1/core/logs/{id}/
```

### System Settings
Used to manage global application settings.
```
GET /api/v1/core/settings/
POST /api/v1/core/settings/
GET /api/v1/core/settings/{id}/
PUT /api/v1/core/settings/{id}/
PATCH /api/v1/core/settings/{id}/
DELETE /api/v1/core/settings/{id}/
```

## Query Parameters

### Pagination
```
?page=1&page_size=20
```

### Filtering
```
?endpoint=/api/v1/core/settings/&method=GET
```

### Search
```
?search=term
```

### Ordering
```
?ordering=created_at
?ordering=-created_at
```

## Response Format

### Success Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "key": "example_key"
  },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "ERROR_CODE",
  "message": "Error description"
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/core/logs/?page=2",
  "previous": null,
  "results": [...]
}
```

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

## Status Codes

- 200: OK
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error
