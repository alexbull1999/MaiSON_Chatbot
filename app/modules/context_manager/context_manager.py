class ContextManager:
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}

    def add_message(self, message: str, role: str = "user"):
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": message
        })

    def get_context(self) -> dict:
        """Get the current conversation context."""
        return self.current_context

    def update_context(self, new_context: dict):
        """Update the current context with new information."""
        self.current_context.update(new_context)

    def clear_context(self):
        """Clear the current context."""
        self.current_context = {} 