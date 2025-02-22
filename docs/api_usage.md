# MaiSON Chatbot API Usage Guide

## Authentication

All API endpoints require authentication using a bearer token:
```bash
Authorization: Bearer your-api-token
```

## Session Management

The API implements intelligent session management with the following features:

- Anonymous users: Sessions expire after 24 hours of inactivity
- Authenticated users: Sessions expire after 30 days of inactivity
- Property conversations: Remain active until explicitly closed
- Session cookies: Automatically managed for anonymous users
- Session persistence: State is maintained across multiple requests

## Chat Endpoints

### General Chat

Send a general inquiry message to the chatbot:

```bash
POST /api/v1/chat/general
Content-Type: application/json

{
    "message": "Tell me about your services",
    "user_id": "user123",           # Optional for anonymous users
    "session_id": "session123"      # Optional, will be generated if not provided
}
```

Response:
```json
{
    "message": "We offer various real estate services...",
    "conversation_id": 1,
    "session_id": "session123",
    "intent": "general_question",
    "context": {
        "topics_discussed": ["services"],
        "last_intent": "general_question"
    }
}
```

### Property Chat

Send a property-specific message to the chatbot. This endpoint supports bidirectional communication between buyers and sellers:

```bash
POST /api/v1/chat/property
Content-Type: application/json

{
    "message": "Tell me about this property",
    "user_id": "user123",           # Required
    "property_id": "prop123",       # Required
    "role": "buyer",                # Required: either 'buyer' or 'seller'
    "counterpart_id": "seller123",  # Required: ID of the other party
    "session_id": "session123"      # Optional, will be generated if not provided
}
```

Response:
```json
{
    "message": "This property is a luxury apartment...",
    "conversation_id": 1,
    "session_id": "session123",
    "intent": "property_info",
    "property_context": {
        "property_details_requested": true,
        "last_intent": "property_info",
        "role": "buyer",
        "counterpart_id": "seller123"
    }
}
```

## Conversation Management

### Get General Conversation History

```bash
GET /api/v1/conversations/general/{conversation_id}/history
```

Response:
```json
{
    "conversation_id": 1,
    "session_id": "session123",
    "messages": [
        {
            "role": "user",
            "content": "Tell me about your services",
            "timestamp": "2024-03-01T12:00:00Z",
            "intent": "service_inquiry"
        },
        {
            "role": "assistant",
            "content": "We offer various real estate services...",
            "timestamp": "2024-03-01T12:00:01Z",
            "intent": "service_info"
        }
    ],
    "context": {
        "topics_discussed": ["services"],
        "last_intent": "service_info"
    }
}
```

### Get Property Conversation History

```bash
GET /api/v1/conversations/property/{conversation_id}/history
```

Response:
```json
{
    "conversation_id": 1,
    "session_id": "session123",
    "property_id": "prop123",
    "user_id": "user123",
    "role": "buyer",
    "counterpart_id": "seller123",
    "conversation_status": "active",
    "messages": [
        {
            "role": "user",
            "content": "Tell me about this property",
            "timestamp": "2024-03-01T12:00:00Z",
            "intent": "property_info"
        },
        {
            "role": "assistant",
            "content": "This property is a luxury apartment...",
            "timestamp": "2024-03-01T12:00:01Z",
            "intent": "property_details"
        }
    ],
    "property_context": {
        "property_details_requested": true,
        "last_intent": "property_details"
    }
}
```

### Update Property Conversation Status

```bash
PATCH /api/v1/conversations/property/{conversation_id}/status
Content-Type: application/json

{
    "status": "closed"  # One of: 'active', 'pending', 'closed'
}
```

Response:
```json
{
    "message": "Conversation status updated successfully"
}
```

### Get User Conversations

```bash
GET /api/v1/conversations/user/{user_id}?role=buyer&status=active
```

Optional query parameters:
- `role`: Filter by role ('buyer' or 'seller')
- `status`: Filter by status ('active', 'pending', 'closed')

Response:
```json
{
    "general_conversations": [
        {
            "id": 1,
            "session_id": "session123",
            "started_at": "2024-03-01T12:00:00Z",
            "last_message_at": "2024-03-01T12:00:01Z",
            "context": {
                "topics_discussed": ["services"]
            }
        }
    ],
    "property_conversations": [
        {
            "id": 2,
            "session_id": "session456",
            "property_id": "prop123",
            "role": "buyer",
            "counterpart_id": "seller123",
            "conversation_status": "active",
            "started_at": "2024-03-01T12:00:00Z",
            "last_message_at": "2024-03-01T12:00:01Z",
            "property_context": {
                "property_details_requested": true
            }
        }
    ]
}
```

## Intent Classification

The API automatically classifies messages into the following intents:

- `property_inquiry`: Questions about property details
- `availability_and_booking_request`: Viewing and booking requests
- `price_inquiry`: Questions about pricing
- `buyer_seller_communication`: Direct communication between parties
- `negotiation`: Offers and negotiations
- `general_question`: General inquiries
- `unknown`: Unclear or unclassified messages

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid or missing token)
- 404: Not Found (invalid conversation or property ID)
- 422: Validation Error (invalid request body)
- 500: Internal Server Error

Error response format:
```json
{
    "detail": "Error message with additional details"
}
```

Common error scenarios:
- Invalid session ID: Returns 401 with new session ID
- Expired session: Returns 401 with option to start new session
- Invalid role: Returns 422 with allowed roles
- Missing counterpart: Returns 400 with required fields
- Rate limiting: Returns 429 with retry-after header 