from typing import Dict, List, Optional

class Property:
    def __init__(self, id: str, name: str, type: str, location: str):
        self.id = id
        self.name = name
        self.type = type
        self.location = location

class PropertyContextModule:
    def __init__(self):
        self.properties: Dict[str, Property] = {}
        self.current_property: Optional[Property] = None

    def add_property(self, property: Property):
        """Add a property to the context."""
        self.properties[property.id] = property

    def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by its ID."""
        return self.properties.get(property_id)

    def set_current_property(self, property_id: str) -> bool:
        """Set the current property context."""
        if property_id in self.properties:
            self.current_property = self.properties[property_id]
            return True
        return False

    def get_current_property(self) -> Optional[Property]:
        """Get the current property in context."""
        return self.current_property

    def clear_current_property(self):
        """Clear the current property context."""
        self.current_property = None 