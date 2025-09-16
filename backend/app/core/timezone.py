"""Timezone utilities for consistent IST usage across the application."""

from datetime import datetime, timezone, timedelta
from typing import Optional
import pytz

# Indian Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')

def now() -> datetime:
    """Get current datetime in IST."""
    return datetime.now(IST)

def utcnow() -> datetime:
    """Get current datetime in IST (replaces datetime.utcnow())."""
    return datetime.now(IST)

def get_ist_timezone() -> timezone:
    """Get IST timezone object."""
    return timezone(timedelta(hours=5, minutes=30))

def to_ist(dt: datetime) -> datetime:
    """Convert any datetime to IST."""
    if dt.tzinfo is None:
        # Assume naive datetime is in IST
        return IST.localize(dt)
    else:
        # Convert timezone-aware datetime to IST
        return dt.astimezone(IST)

def from_iso_string(iso_string: str) -> datetime:
    """Parse ISO string and convert to IST."""
    # Handle Z suffix (UTC indicator)
    if iso_string.endswith('Z'):
        iso_string = iso_string.replace('Z', '+00:00')
    
    dt = datetime.fromisoformat(iso_string)
    return to_ist(dt)

def ensure_ist(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is in IST, handling None values."""
    if dt is None:
        return None
    return to_ist(dt)

def make_aware(dt: datetime) -> datetime:
    """Make naive datetime timezone-aware in IST."""
    if dt.tzinfo is None:
        return IST.localize(dt)
    return dt

def format_ist(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Format datetime in IST with timezone info."""
    ist_dt = to_ist(dt)
    return ist_dt.strftime(format_str)

# Common IST timezone for SQLAlchemy column defaults
ist_timezone = timezone(timedelta(hours=5, minutes=30))
