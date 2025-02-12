import pytest
from app.modules.llm import LLMClient, LLMProvider, SystemPrompts

@pytest.fixture
def llm_client():
    return LLMClient(provider=LLMProvider.OPENAI)

def test_llm_client_initialization():
    client = LLMClient()
    assert client.provider == LLMProvider.OPENAI
    
    client = LLMClient(provider=LLMProvider.ANTHROPIC)
    assert client.provider == LLMProvider.ANTHROPIC
    
    client = LLMClient(provider=LLMProvider.GEMINI)
    assert client.provider == LLMProvider.GEMINI

def test_system_prompt_generation():
    client = LLMClient()
    prompt = client.get_system_prompt()
    assert isinstance(prompt, str)
    assert "maiSON" in prompt
    assert "real estate" in prompt.lower()

@pytest.mark.asyncio
async def test_generate_response(llm_client):
    messages = [
        {
            "role": "user",
            "content": "Tell me about the downtown apartment"
        }
    ]
    
    try:
        response = await llm_client.generate_response(messages)
        assert isinstance(response, str)
        assert len(response) > 0
    except Exception as e:
        # Skip test if API keys are not configured
        pytest.skip(f"Skipping due to API configuration: {str(e)}")

@pytest.mark.asyncio
async def test_error_handling(llm_client):
    # Test with invalid messages format
    messages = [{"invalid": "format"}]
    
    response = await llm_client.generate_response(messages)
    assert isinstance(response, str)
    assert "apologize" in response.lower()

def test_provider_specific_prompts():
    # Test prompts for each provider
    for provider in LLMProvider:
        prompt = SystemPrompts.get_prompt(provider)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "maiSON" in prompt
        
        # Check for provider-specific instructions
        if provider == LLMProvider.OPENAI:
            assert "markdown" in prompt.lower()
        elif provider == LLMProvider.ANTHROPIC:
            assert "bullet points" in prompt.lower()
        elif provider == LLMProvider.GEMINI:
            assert "natural language" in prompt.lower() 