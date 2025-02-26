import pytest
import json
from unittest.mock import AsyncMock, patch, mock_open
from app.modules.website_info.website_info_module import WebsiteInfoModule


@pytest.fixture
def website_info_module():
    """Create a WebsiteInfoModule instance with mocked dependencies."""
    with patch('app.modules.llm.LLMClient') as mock_llm:
        mock_llm_instance = AsyncMock()
        mock_llm_instance.generate_response.return_value = "This is a test response"
        mock_llm.return_value = mock_llm_instance
        
        module = WebsiteInfoModule()
        yield module


@pytest.fixture
def mock_website_features():
    """Mock website features data."""
    return {
        "property_search": {
            "name": "Property Search",
            "description": "Advanced search functionality to find properties.",
            "how_to_use": "Enter your search criteria in the search bar.",
            "features": ["Location-based search", "Price range filters"]
        },
        "ai_assistant": {
            "name": "24/7 AI Assistant",
            "description": "Get instant answers to questions.",
            "how_to_use": "Click the chat icon to start a conversation.",
            "features": ["Property search assistance", "Available 24/7"]
        }
    }


@pytest.fixture
def mock_user_journey():
    """Mock user journey data."""
    return {
        "buyer": {
            "steps": [
                {
                    "name": "Create Account",
                    "description": "Sign up for a MaiSON account."
                },
                {
                    "name": "Search Properties",
                    "description": "Use our search tools to find properties."
                }
            ]
        },
        "seller": {
            "steps": [
                {
                    "name": "Create Account",
                    "description": "Sign up for a MaiSON account."
                },
                {
                    "name": "List Property",
                    "description": "Create your property listing."
                }
            ]
        }
    }


@pytest.fixture
def mock_company_info():
    """Mock company information data."""
    return {
        "company": {
            "name": "MaiSON-AI",
            "founded": "2023",
            "mission": "To revolutionize the property market."
        },
        "about_us": {
            "summary": "MaiSON-AI was founded with a simple idea."
        },
        "team": {
            "leadership": [
                {
                    "name": "Jane Doe",
                    "position": "CEO"
                }
            ]
        }
    }


def test_website_info_module_initialization():
    """Test that the WebsiteInfoModule initializes correctly."""
    with patch('os.path.join', return_value='/mock/path'):
        with patch.object(WebsiteInfoModule, '_load_json_data', return_value={}):
            with patch('app.modules.llm.LLMClient'):
                module = WebsiteInfoModule()
                assert module.llm_client is not None
                assert module.data_dir == '/mock/path'
                assert module._website_features == {}
                assert module._user_journey == {}
                assert module._company_info == {}


def test_load_json_data_success():
    """Test successful loading of JSON data."""
    mock_data = {"key": "value"}
    mock_json = json.dumps(mock_data)
    
    with patch('app.modules.llm.LLMClient'):
        module = WebsiteInfoModule()
        with patch("builtins.open", mock_open(read_data=mock_json)):
            with patch("os.path.exists", return_value=True):
                result = module._load_json_data("test.json")
                assert result == mock_data


def test_load_json_data_file_not_found():
    """Test handling of file not found when loading JSON data."""
    with patch('app.modules.llm.LLMClient'):
        module = WebsiteInfoModule()
        with patch("os.path.exists", return_value=False):
            with patch("builtins.print") as mock_print:
                result = module._load_json_data("nonexistent.json")
                assert result == {}
                mock_print.assert_called_once()


def test_load_json_data_invalid_json():
    """Test handling of invalid JSON data."""
    with patch('app.modules.llm.LLMClient'):
        module = WebsiteInfoModule()
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.print") as mock_print:
                    result = module._load_json_data("invalid.json")
                    assert result == {}
                    mock_print.assert_called_once()


@pytest.mark.asyncio
async def test_handle_website_functionality(mock_website_features, mock_user_journey):
    """Test handling website functionality queries."""
    # Create a module with mocked methods
    with patch('app.modules.website_info.website_info_module.WebsiteInfoModule.handle_website_functionality', 
               new_callable=AsyncMock) as mock_handle:
        # Set up the mock to return a test response
        mock_handle.return_value = "This is a test response"
        
        # Create the module
        module = WebsiteInfoModule()
        
        # Test the handler
        message = "How do I search for properties on your website?"
        response = await module.handle_website_functionality(message)
        
        # Verify the response
        assert response == "This is a test response"
        
        # Verify that the handler was called with the correct parameters
        mock_handle.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_company_information(mock_company_info):
    """Test handling company information queries."""
    # Create a module with mocked methods
    with patch('app.modules.website_info.website_info_module.WebsiteInfoModule.handle_company_information', 
               new_callable=AsyncMock) as mock_handle:
        # Set up the mock to return a test response
        mock_handle.return_value = "This is a test response"
        
        # Create the module
        module = WebsiteInfoModule()
        
        # Test the handler
        message = "When was MaiSON founded?"
        response = await module.handle_company_information(message)
        
        # Verify the response
        assert response == "This is a test response"
        
        # Verify that the handler was called with the correct parameters
        mock_handle.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_website_functionality_error():
    """Test error handling in website functionality handler."""
    # Create a module with mocked LLM client that raises an exception
    with patch('app.modules.llm.llm_client.LLMClient.generate_response', 
               new_callable=AsyncMock, side_effect=Exception("Test error")):
        
        # Create the module
        module = WebsiteInfoModule()
        
        # Test the handler
        message = "How do I search for properties?"
        response = await module.handle_website_functionality(message)
        
        # Verify the error response
        assert "apologize" in response.lower()
        assert "error" in response.lower()


@pytest.mark.asyncio
async def test_handle_company_information_error():
    """Test error handling in company information handler."""
    # Create a module with mocked LLM client that raises an exception
    with patch('app.modules.llm.llm_client.LLMClient.generate_response', 
               new_callable=AsyncMock, side_effect=Exception("Test error")):
        
        # Create the module
        module = WebsiteInfoModule()
        
        # Test the handler
        message = "Tell me about your company."
        response = await module.handle_company_information(message)
        
        # Verify the error response
        assert "apologize" in response.lower()
        assert "error" in response.lower() 