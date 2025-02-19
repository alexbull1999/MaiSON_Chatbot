# maiSON Chatbot API Usage Guide

## Authentication

All API endpoints require authentication using a bearer token:
```bash
Authorization: Bearer your-api-token
```

## Chat Endpoints

### General Chat

Send a general inquiry message to the chatbot:

```bash
POST /api/chat/general
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
    "intent": "service_inquiry",
    "context": {
        "topics_discussed": ["services"],
        "last_intent": "service_inquiry"
    }
}
```

### Property Chat

Send a property-specific message to the chatbot:

```bash
POST /api/chat/property
Content-Type: application/json

{
    "message": "Tell me about this property",
    "user_id": "user123",           # Required
    "property_id": "prop123",       # Required
    "seller_id": "seller123",       # Required
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
        "last_intent": "property_info"
    }
}
```

## Conversation Management

### Get General Conversation History

```bash
GET /api/conversations/general/{conversation_id}/history
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
GET /api/conversations/property/{conversation_id}/history
```

Response:
```json
{
    "conversation_id": 1,
    "session_id": "session123",
    "property_id": "prop123",
    "seller_id": "seller123",
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

### Get User Conversations

```bash
GET /api/conversations/user/{user_id}
```

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
            "seller_id": "seller123",
            "started_at": "2024-03-01T12:00:00Z",
            "last_message_at": "2024-03-01T12:00:01Z",
            "property_context": {
                "property_details_requested": true
            }
        }
    ]
}
```

## Conversation Management

### Get General Conversation History

```bash
GET /api/conversations/general/{conversation_id}/history
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
GET /api/conversations/property/{conversation_id}/history
```

Response:
```json
{
    "conversation_id": 1,
    "session_id": "session123",
    "property_id": "prop123",
    "seller_id": "seller123",
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

### Get User Conversations

```bash
GET /api/conversations/user/{user_id}
```

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
            "seller_id": "seller123",
            "started_at": "2024-03-01T12:00:00Z",
            "last_message_at": "2024-03-01T12:00:01Z",
            "property_context": {
                "property_details_requested": true
            }
        }
    ]
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

Error response format:
```json
{
    "detail": "Error message with additional details"
}
``` 