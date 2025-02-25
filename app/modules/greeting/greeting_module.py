from typing import Dict, Optional
import random
from ..llm import LLMClient, LLMProvider

class GreetingModule:
    """Module for handling greeting messages with personalized responses."""
    
    def __init__(self):
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)
        self.greeting_templates = [
            "Hello! Welcome to MaiSON. How can I assist you with your property search today?",
            "Hi there! I'm your MaiSON property assistant. What kind of property information are you looking for?",
            "Welcome! I'm here to help you find your perfect property. What would you like to know?",
            "Greetings! I'm your MaiSON AI assistant. How can I help with your property journey today?",
            "Hello and welcome to MaiSON! Whether you're buying, selling, or just exploring, I'm here to help!"
        ]

    async def handle_greeting(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Handle greeting messages with personalized responses.
        Takes into account user context if available.
        """
        try:
            # If we have user context, generate a personalized response using LLM
            if context and (context.get('user_id') or context.get('user_name')):
                prompt = (
                    f"Generate a warm, friendly greeting response to: '{message}'\n"
                    f"Context: {str(context)}\n"
                    "The response should be welcoming and mention that you can help with property-related questions."
                )
                
                response = await self.llm_client.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    module_name="greeting"
                )
                
                if response:
                    return response

            # Fallback to template if LLM fails or no context
            return random.choice(self.greeting_templates)

        except Exception as e:
            print(f"Error in greeting module: {str(e)}")
            return self.greeting_templates[0]  # Return default greeting on error 