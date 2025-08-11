import requests
from .config import settings

def geocode_il(address: str) -> tuple[float, float]:
    # Using OpenStreetMap Nominatim (public). Respect usage policies for production.
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "countrycodes": "il",
    }
    headers = {"User-Agent": "EventConsole/1.0 (contact: admin@example.com)"}
    r = requests.get(settings.NOMINATIM_URL, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError("Address not found in IL")
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])
    return lat, lon