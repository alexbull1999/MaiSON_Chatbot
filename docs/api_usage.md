# maiSON Chatbot API Usage Guide

## Authentication

All API endpoints require authentication using a bearer token:
```bash
Authorization: Bearer your-api-token
```

## Endpoints

### Chat Endpoint

Send a message to the chatbot:

```bash
POST /chat
Content-Type: application/json

{
    "message": "Tell me about the downtown apartment"
}
```

Response:
```json
{
    "message": "The downtown apartment is a luxury property...",
    "intent": "property_inquiry",
    "context": {
        "property_id": "123"
    }
}
```

### Property Management

#### List Properties

```bash
GET /properties
```

Response:
```json
{
    "properties": [
        {
            "id": "123",
            "name": "Luxury Downtown Apartment",
            "type": "Apartment",
            "location": "Downtown",
            "price": 2500.00
        }
    ]
}
```

#### Get Property Details

```bash
GET /properties/{property_id}
```

Response:
```json
{
    "id": "123",
    "name": "Luxury Downtown Apartment",
    "type": "Apartment",
    "location": "Downtown",
    "price": 2500.00,
    "description": "Modern luxury apartment...",
    "availability": [
        {
            "start_date": "2024-03-01T00:00:00Z",
            "end_date": "2024-03-02T00:00:00Z",
            "is_available": true
        }
    ]
}
```

### Availability

Check property availability:

```bash
GET /properties/{property_id}/availability
```

Response:
```json
{
    "availability": [
        {
            "start_date": "2024-03-01T00:00:00Z",
            "end_date": "2024-03-02T00:00:00Z",
            "is_available": true
        }
    ]
}
```

### Inquiries

Submit an inquiry:

```bash
POST /inquiries
Content-Type: application/json

{
    "property_id": "123",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "message": "I'm interested in viewing this property"
}
```

Response:
```json
{
    "inquiry_id": "456",
    "status": "pending",
    "created_at": "2024-03-01T12:00:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

Error response format:
```json
{
    "error": "Error message",
    "detail": "Additional error details"
}
``` 