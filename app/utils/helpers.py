from datetime import datetime, timedelta

def format_datetime(dt: datetime) -> str:
    """Format datetime to string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_date_range(dt: datetime) -> tuple[datetime, datetime]:
    """Parse date range string into start and end dates."""
    # TODO: Implement proper date range parsing
    today = datetime.now()
    return today, today + timedelta(days=7)

def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[1]

def sanitize_input(text: str) -> str:
    """Sanitize user input."""
    return text.strip()

def format_price(price: float) -> str:
    """Format price with currency."""
    return f"${price:,.2f}" 