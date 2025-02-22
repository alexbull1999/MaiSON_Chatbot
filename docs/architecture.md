# MaiSON Chatbot Architecture

## Overview

The MaiSON Chatbot is a microservice-based application designed to handle property-related inquiries and provide intelligent responses. The system is built using FastAPI and follows a modular architecture for maintainability and scalability.

## Core Components

### 1. Message Router
- Central component that orchestrates message flow
- Handles incoming messages and routes them to appropriate modules
- Manages conversation context and state

### 2. Intent Classification
- Analyzes user messages to determine intent
- Uses keyword-based classification (to be enhanced with ML/NLP)
- Supports multiple intent types (property inquiry, availability, pricing, etc.)

### 3. Context Management
- Maintains conversation context
- Tracks current property context
- Stores conversation history

### 4. Property Context
- Manages property-related information
- Handles property queries and updates
- Maintains property availability status

### 5. Advisory Module
- Generates property recommendations
- Provides market analysis
- Offers property insights

### 6. Communication Module
- Handles message formatting
- Manages response templates
- Ensures consistent communication style

## Database Schema

The application uses SQLAlchemy ORM with the following main tables:
- Properties
- AvailabilitySlots
- Inquiries

## API Endpoints

The service exposes RESTful endpoints for:
- Chat interactions
- Property management
- Availability checking
- User inquiries

## Future Enhancements

1. Integration with ML/NLP services for better intent classification
2. Real-time property updates
3. Integration with external property databases
4. Enhanced recommendation system
5. Multi-language support 