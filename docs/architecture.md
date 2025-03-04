# MaiSON Chatbot Architecture

## Overview

The MaiSON Chatbot is a microservice-based application designed to handle property-related inquiries and provide intelligent responses. The system is built using FastAPI and follows a modular architecture for maintainability and scalability. It supports both general property inquiries and bidirectional communication between buyers and sellers.

## Core Components

### 1. Message Router
- Central component that orchestrates message flow
- Handles incoming messages and routes them to appropriate modules
- Manages conversation context and state
- Enforces chat type restrictions (general vs. property)
- Supports bidirectional communication routing

### 2. Intent Classification
- Analyzes user messages to determine intent using LLM
- Supports multiple intent types:
  - Property inquiry
  - Availability and booking
  - Price inquiry
  - Buyer-seller communication
  - Negotiation
  - General questions
- Provides confidence scores for intent classification
- Handles fallback for unclear intents

### 3. Session Management
- Manages user sessions with configurable TTLs:
  - Anonymous sessions (24-hour expiry)
  - Authenticated sessions (30-day expiry)
  - Property conversations (no automatic expiry)
- Handles session cleanup via background tasks
- Provides session validation and refresh mechanisms
- Manages cookie-based session tracking

### 4. Context Management
- Maintains conversation context
- Tracks current property context
- Stores conversation history
- Supports context switching between conversations
- Preserves context across session refreshes

### 5. Property Context Module
- Manages property-related information
- Handles property queries and updates
- Maintains property availability status
- Implements caching for property data
- Integrates with external property services
- Provides area insights and market analysis

### 6. Communication Module
- Handles message formatting
- Manages response templates
- Ensures consistent communication style
- Supports buyer-seller message forwarding
- Implements notification handling
- Provides message type classification

### 7. Data Integration
- Implements caching mechanisms:
  - Property data cache
  - Area insights cache
  - Market data cache
- Integrates with external services:
  - Property listings API
  - OpenStreetMap for location data
  - Market data providers
- Manages data refresh and invalidation

### 8. Advisory Module
- Generates property recommendations
- Provides market analysis
- Offers property insights
- Analyzes area characteristics
- Generates location-based insights
- Provides investment advice

## Database Schema

The application uses SQLAlchemy ORM with the following main tables:

### Conversation Tables
- `general_conversations`: Tracks general chat sessions
- `general_messages`: Stores messages for general conversations
- `property_conversations`: Manages buyer-seller communications
- `property_messages`: Stores property-specific messages

### Reference Tables
- `external_references`: Links to external service data

## API Endpoints

The service exposes RESTful endpoints for:

### Chat Operations
- General chat interactions
- Property-specific communications
- Buyer-seller message exchange
- Conversation history retrieval

### Session Management
- Session creation and validation
- Session refresh operations
- Status updates for conversations

### User Operations
- User conversation history
- Role-based conversation filtering
- Conversation status management

## Security Features

- Bearer token authentication
- Session-based security
- CORS protection
- Rate limiting
- Secure cookie handling
- Input validation

## Background Tasks

- Session cleanup (hourly)
- Cache invalidation
- Data synchronization
- Notification processing

## Future Enhancements

1. Enhanced ML/NLP capabilities for intent classification
2. Real-time property updates via WebSocket
3. Integration with additional property databases
4. Enhanced recommendation system using ML
5. Multi-language support
6. Advanced analytics and reporting
7. Mobile push notifications
8. Voice interface support 