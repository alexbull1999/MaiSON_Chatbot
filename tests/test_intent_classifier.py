import pytest
from app.modules.intent_classification.intent_classifier import IntentClassifier, Intent

def test_intent_classifier_initialization():
    classifier = IntentClassifier()
    assert classifier.intents is not None

def test_property_inquiry_intent():
    classifier = IntentClassifier()
    message = "Can you tell me about this property?"
    intent = classifier.classify(message)
    assert intent == Intent.PROPERTY_INQUIRY

def test_availability_check_intent():
    classifier = IntentClassifier()
    message = "When is this property available?"
    intent = classifier.classify(message)
    assert intent == Intent.AVAILABILITY_CHECK

def test_price_inquiry_intent():
    classifier = IntentClassifier()
    message = "How much does it cost?"
    intent = classifier.classify(message)
    assert intent == Intent.PRICE_INQUIRY

def test_booking_request_intent():
    classifier = IntentClassifier()
    message = "I would like to book this property"
    intent = classifier.classify(message)
    assert intent == Intent.BOOKING_REQUEST

def test_general_question_intent():
    classifier = IntentClassifier()
    message = "Thank you for your help"
    intent = classifier.classify(message)
    assert intent == Intent.GENERAL_QUESTION 