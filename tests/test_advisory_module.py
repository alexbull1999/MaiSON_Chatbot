import pytest
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.modules.advisory.advisory_module import AdvisoryModule
from app.modules.property_context.property_context_module import Property

def test_advisory_module_initialization():
    advisory = AdvisoryModule()
    assert isinstance(advisory.recommendations, dict)

def test_get_property_recommendations():
    advisory = AdvisoryModule()
    user_preferences = {
        "type": "Apartment",
        "location": "Test Location",
        "max_price": 1000
    }
    recommendations = advisory.get_property_recommendations(user_preferences)
    assert isinstance(recommendations, list)

def test_generate_property_insights():
    advisory = AdvisoryModule()
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    insights = advisory.generate_property_insights(test_property)
    assert isinstance(insights, list)
    assert len(insights) > 0
    assert any("Property Type: Apartment" in insight for insight in insights)
    assert any("Location: Test Location" in insight for insight in insights)

def test_get_market_analysis():
    advisory = AdvisoryModule()
    analysis = advisory.get_market_analysis("Test Location")
    assert isinstance(analysis, dict)
    assert "market_trend" in analysis
    assert "average_price" in analysis
    assert "demand_level" in analysis 