from typing import List, Dict, Optional
import openai
from openai import OpenAI
import anthropic
import google.generativeai as genai
from .types import LLMProvider
from .prompts import SystemPrompts
import os
from functools import lru_cache
from app.config import settings

class LLMClient:
    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI):
        self.provider = provider
        self._setup_client()

    def _setup_client(self):
        """Initialize the appropriate LLM client based on provider."""
        try:
            if self.provider == LLMProvider.OPENAI:
                api_key = settings.openai_api_key
                if not api_key or api_key.startswith("sk-dummy"):
                    print("Warning: Using mock responses as OpenAI API key is not configured")
                    self.client = None
                else:
                    self.client = OpenAI(api_key=api_key)
            elif self.provider == LLMProvider.ANTHROPIC:
                api_key = settings.anthropic_api_key
                if not api_key or api_key.startswith("sk-ant-dummy"):
                    print("Warning: Using mock responses as Anthropic API key is not configured")
                    self.client = None
                else:
                    self.client = anthropic.Anthropic(api_key=api_key)
            elif self.provider == LLMProvider.GEMINI:
                api_key = settings.google_api_key
                # Debug: Print first and last 4 characters of the API key
                if api_key:
                    masked_key = f"{api_key[:4]}...{api_key[-4:]}"
                    print(f"Debug: Found Google API key: {masked_key}")
                
                if not api_key or api_key == "dummy-key":
                    print("Warning: Using mock responses as Google API key is not configured")
                    self.client = None
                else:
                    genai.configure(api_key=api_key)
                    self.client = genai.GenerativeModel('gemini-pro')
                    print("Debug: Successfully configured Gemini client")
        except Exception as e:
            print(f"Warning: Error setting up LLM client ({str(e)}). Using mock responses.")
            self.client = None

    def _get_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a mock response for testing purposes."""
        try:
            last_message = messages[-1]["content"].lower()
        except KeyError:
            return "I apologize, I didn't understand that message format."

        
        if "property" in last_message or "house" in last_message or "apartment" in last_message:
            return "This is a beautiful property with 3 bedrooms, 2 bathrooms, and a modern kitchen. It's located in a great neighborhood with easy access to public transportation."
        elif "price" in last_message or "cost" in last_message:
            return "The property is priced at $2,500 per month, which is competitive for this area. This includes basic utilities and maintenance."
        elif "available" in last_message or "when" in last_message:
            return "The property is available for viewing this week. We have slots available on Wednesday afternoon and Friday morning."
        else:
            return "I'm here to help you with any questions about our properties. What would you like to know?"

    @lru_cache(maxsize=1)
    def get_system_prompt(self) -> str:
        """Get the appropriate system prompt for the current provider."""
        return SystemPrompts.get_prompt(self.provider)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response using the configured LLM provider.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum length of the response
            
        Returns:
            Generated response text
        """
        try:
            # If no client is available, use mock responses
            if self.client is None:
                return self._get_mock_response(messages)

            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai_response(messages, temperature, max_tokens)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic_response(messages, temperature, max_tokens)
            elif self.provider == LLMProvider.GEMINI:
                return await self._generate_gemini_response(messages, temperature, max_tokens)
        except Exception as e:
            # Log the error and return a fallback response
            print(f"Error generating LLM response: {str(e)}")
            return self._get_mock_response(messages)

    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response using OpenAI's API."""
        # Add system prompt if not present
        if not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {
                "role": "system",
                "content": self.get_system_prompt()
            })

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or gpt-3.5-turbo for lower cost
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def _generate_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response using Anthropic's Claude API."""
        # Convert messages to Claude format
        system_prompt = self.get_system_prompt()
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})

        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=formatted_messages
        )
        return response.content[0].text

    async def _generate_gemini_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response using Google's Gemini API."""
        try:
            # Prepare messages for Gemini
            formatted_content = []
            
            # Add system prompt
            system_prompt = self.get_system_prompt()
            formatted_content.append(system_prompt)
            
            # Add conversation history
            for msg in messages:
                role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                formatted_content.append(f"{role_prefix}{msg['content']}")
            
            # Join all content with newlines
            final_prompt = "\n".join(formatted_content)
            
            print(f"Debug: Sending request to Gemini API with prompt: {final_prompt}")
            
            # Use synchronous API
            response = self.client.generate_content(
                final_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            if not response or not response.text:
                print("Warning: Received empty response from Gemini API")
                return self._get_mock_response(messages)
                
            print(f"Debug: Received response from Gemini API: {response.text}")
            return response.text
            
        except Exception as e:
            print(f"Error in Gemini API call: {str(e)}")
            return self._get_mock_response(messages) 