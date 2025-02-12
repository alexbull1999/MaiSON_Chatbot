import pytest
from app.modules.context_manager.context_manager import ContextManager

def test_context_manager_initialization():
    manager = ContextManager()
    assert manager.conversation_history == []
    assert manager.current_context == {}

def test_add_message():
    manager = ContextManager()
    test_message = "Hello, how are you?"
    manager.add_message(test_message)
    assert len(manager.conversation_history) == 1
    assert manager.conversation_history[0]["content"] == test_message
    assert manager.conversation_history[0]["role"] == "user"

def test_update_context():
    manager = ContextManager()
    test_context = {"property_id": "123"}
    manager.update_context(test_context)
    assert manager.current_context == test_context

def test_clear_context():
    manager = ContextManager()
    test_context = {"property_id": "123"}
    manager.update_context(test_context)
    manager.clear_context()
    assert manager.current_context == {} 