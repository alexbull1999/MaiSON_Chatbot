from typing import List, Dict, Optional
import anthropic
import google.generativeai as genai
from openai import OpenAI
from .types import LLMProvider
from .prompts import SystemPrompts
from functools import lru_cache
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMClient:
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.GEMINI,
        fallback_providers: List[LLMProvider] = None
    ):
        self.provider = provider
        self.fallback_providers = (
            fallback_providers or [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
        )
        self.clients = {}
        self._setup_clients()

    def _setup_clients(self):
        """Initialize all available LLM clients."""
        # Setup OpenAI
        api_key = settings.openai_api_key
        if api_key and not api_key.startswith("sk-dummy"):
            self.clients[LLMProvider.OPENAI] = OpenAI(api_key=api_key)

        # Setup Anthropic
        api_key = settings.anthropic_api_key
        if api_key and not api_key.startswith("sk-ant-dummy"):
            self.clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(api_key=api_key)

        # Setup Gemini
        api_key = settings.google_api_key
        if api_key and api_key != "dummy-key":
            genai.configure(api_key=api_key)
            self.clients[LLMProvider.GEMINI] = genai.GenerativeModel('gemini-2.0-flash')

    def _get_mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a mock response for testing purposes."""
        try:
            last_message = messages[-1]["content"].lower()
        except KeyError:
            return "I apologize, I didn't understand that message format."

        if "property" in last_message or "house" in last_message:
            return (
                "This is a beautiful property with 3 bedrooms, 2 bathrooms, "
                "and a modern kitchen. It's located in a great neighborhood "
                "with easy access to public transportation."
            )
        elif "price" in last_message or "cost" in last_message:
            return (
                "The property is priced at $2,500 per month, which is competitive "
                "for this area. This includes basic utilities and maintenance."
            )
        elif "available" in last_message or "when" in last_message:
            return (
                "The property is available for viewing this week. We have slots "
                "available on Wednesday afternoon and Friday morning."
            )
        else:
            return (
                "I'm here to help you with any questions about our properties. "
                "What would you like to know?"
            )

    @lru_cache(maxsize=1)
    def get_system_prompt(self) -> str:
        """Get the appropriate system prompt for the current provider."""
        return SystemPrompts.get_prompt(self.provider)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        module_name: Optional[str] = None,
    ) -> str:
        """
        Generate a response using the configured LLM provider.
        Now includes system prompt in all requests.
        """
        try:
            # Get appropriate system prompt based on module
            system_prompt = (
                SystemPrompts.get_module_prompt(module_name, self.provider)
                if module_name
                else SystemPrompts.get_prompt(self.provider)
            )

            # Try primary provider first
            if self.provider in self.clients:
                try:
                    response = await self._generate_with_provider(
                        self.provider,
                        messages,
                        temperature,
                        max_tokens,
                        system_prompt
                    )
                    if response:
                        return response
                except Exception as e:
                    print(f"Error with primary provider {self.provider}: {str(e)}")

            # Try fallback providers
            for provider in self.fallback_providers:
                if provider in self.clients:
                    try:
                        print(f"Trying fallback provider: {provider}")
                        # Update system prompt for fallback provider
                        fallback_system_prompt = (
                            SystemPrompts.get_module_prompt(module_name, provider)
                            if module_name
                            else SystemPrompts.get_prompt(provider)
                        )
                        response = await self._generate_with_provider(
                            provider,
                            messages,
                            temperature,
                            max_tokens,
                            fallback_system_prompt
                        )
                        if response:
                            return response
                    except Exception as e:
                        print(f"Error with fallback provider {provider}: {str(e)}")
                        continue

            # If all providers fail, use mock response
            return self._get_mock_response(messages)

        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error generating a response. Please try again."

    async def _generate_with_provider(
        self,
        provider: LLMProvider,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        system_prompt: str
    ) -> str:
        """Generate response using a specific provider."""
        if provider == LLMProvider.OPENAI:
            return await self._generate_openai_response(
                messages, temperature, max_tokens, system_prompt
            )
        elif provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic_response(
                messages, temperature, max_tokens, system_prompt
            )
        elif provider == LLMProvider.GEMINI:
            return await self._generate_gemini_response(
                messages, temperature, max_tokens, system_prompt
            )
        
        raise ValueError(f"Unsupported provider: {provider}")

    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        system_prompt: str
    ) -> str:
        """Generate response using OpenAI's API."""
        # Add system prompt if not present
        if not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })

        response = await self.clients[LLMProvider.OPENAI].chat.completions.create(
            model="gpt-4o-latest",  # or gpt-3.5-turbo for lower cost
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def _generate_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        system_prompt: str
    ) -> str:
        """Generate response using Anthropic's Claude API."""
        # Convert messages to Claude format
        formatted_messages = []
        
        for msg in messages:
            if msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})

        response = await self.clients[LLMProvider.ANTHROPIC].messages.create(
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
        max_tokens: int,
        system_prompt: str
    ) -> str:
        """Generate response using Google's Gemini API."""
        try:
            # Prepare messages for Gemini
            formatted_content = []
            
            # Add system prompt
            formatted_content.append(system_prompt)
            
            # Add conversation history
            for msg in messages:
                role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                formatted_content.append(f"{role_prefix}{msg['content']}")
            
            # Join all content with newlines
            final_prompt = "\n".join(formatted_content)
            
            print(f"Debug: Sending request to Gemini API with prompt: {final_prompt}")
            
            # Use synchronous API with async wrapper
            response = await self._run_sync_gemini(
                final_prompt,
                temperature,
                max_tokens
            )
            
            if not response or not response.text:
                print("Warning: Received empty response from Gemini API")
                return self._get_mock_response(messages)
                
            print(f"Debug: Received response from Gemini API: {response.text}")
            return response.text
            
        except Exception as e:
            print(f"Error in Gemini API call: {str(e)}")
            return self._get_mock_response(messages)

    async def _run_sync_gemini(self, prompt: str, temperature: float, max_tokens: int):
        """Run Gemini's synchronous API in an async context."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.clients[LLMProvider.GEMINI].generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
        ) 