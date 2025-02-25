import pytest
from unittest.mock import AsyncMock
from app.modules.greeting.greeting_module import GreetingModule

@pytest.fixture
def greeting_module():
    """Create a GreetingModule instance with mocked dependencies."""
    module = GreetingModule()
    module.llm_client = AsyncMock()
    return module

@pytest.mark.asyncio
async def test_handle_greeting_with_context(greeting_module):
    """Test handling a greeting with user context."""
    # Mock LLM response
    greeting_module.llm_client.generate_response.return_value = "Hello John! Welcome to MaiSON."
    
    # Test with user context
    context = {"user_name": "John", "user_id": "123"}
    response = await greeting_module.handle_greeting("Hi", context)
    
    # Verify response
    assert isinstance(response, str)
    assert "John" in response
    assert "MaiSON" in response
    
    # Verify LLM client call
    greeting_module.llm_client.generate_response.assert_called_once()
    call_args = greeting_module.llm_client.generate_response.call_args[1]
    assert call_args.get('module_name') == 'greeting'
    assert call_args.get('temperature') == 0.7

@pytest.mark.asyncio
async def test_handle_greeting_without_context(greeting_module):
    """Test handling a greeting without user context."""
    response = await greeting_module.handle_greeting("Hello", None)
    
    # Verify response is from templates
    assert isinstance(response, str)
    assert any(response == template for template in greeting_module.greeting_templates)
    
    # Verify LLM client was not called
    greeting_module.llm_client.generate_response.assert_not_called()

@pytest.mark.asyncio
async def test_handle_greeting_with_error(greeting_module):
    """Test handling a greeting when LLM client fails."""
    # Mock LLM to raise an exception
    greeting_module.llm_client.generate_response.side_effect = Exception("Test error")
    
    # Test with context
    context = {"user_name": "John", "user_id": "123"}
    response = await greeting_module.handle_greeting("Hi", context)
    
    # Verify fallback to default template
    assert response == greeting_module.greeting_templates[0]
    
    # Verify LLM client was called but failed
    greeting_module.llm_client.generate_response.assert_called_once()
    call_args = greeting_module.llm_client.generate_response.call_args[1]
    assert call_args.get('module_name') == 'greeting' 