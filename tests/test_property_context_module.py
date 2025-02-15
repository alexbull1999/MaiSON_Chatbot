from app.modules.property_context.property_context_module import PropertyContextModule, Property

def test_property_context_initialization():
    context = PropertyContextModule()
    assert context.properties == {}
    assert context.current_property is None

def test_add_property():
    context = PropertyContextModule()
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    context.add_property(test_property)
    assert test_property.id in context.properties
    assert context.properties[test_property.id] == test_property

def test_get_property():
    context = PropertyContextModule()
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    context.add_property(test_property)
    retrieved_property = context.get_property("123")
    assert retrieved_property == test_property

def test_set_current_property():
    context = PropertyContextModule()
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    context.add_property(test_property)
    
    # Test setting existing property
    assert context.set_current_property("123") is True
    assert context.current_property == test_property
    
    # Test setting non-existent property
    assert context.set_current_property("456") is False 