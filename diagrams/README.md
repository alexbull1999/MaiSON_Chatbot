# MaiSON Chatbot System Diagrams

This directory contains diagrams that illustrate the architecture and functionality of the MaiSON Chatbot system.

## Diagrams Overview

### Architecture Diagram (`architecture_diagram.md`)

The architecture diagram provides a high-level overview of the MaiSON Chatbot system, showing the key components and their relationships. It illustrates:

- The main API layer and routing components
- The message routing and intent classification system
- The specialized modules for different types of inquiries
- The data services and external API integrations
- The database structure
- The LLM integration throughout the system

This diagram helps understand how the different components of the system interact with each other.

### Database Schema Diagram (`database_schema.md`)

The database schema diagram shows the structure of the database, including:

- The `GeneralConversation` and `GeneralMessage` tables for general inquiries
- The `PropertyConversation` and `PropertyMessage` tables for property-specific conversations
- The `ExternalReference` table for tracking references to external services
- The relationships between these tables
- The key fields and their data types

This diagram helps understand how conversation data is stored and organized in the database.

## Viewing the Diagrams

These diagrams are created using Mermaid, a markdown-based diagramming tool. To view them:

1. Open the `.md` files in a Markdown viewer that supports Mermaid syntax
2. Use the GitHub web interface, which natively renders Mermaid diagrams
3. Use a Mermaid live editor (https://mermaid.live/) by copying the diagram code

## Updating the Diagrams

If you need to update these diagrams:

1. Edit the corresponding `.md` file
2. Modify the Mermaid code between the triple backticks
3. Preview the changes using one of the methods mentioned above
4. Commit the changes to the repository 