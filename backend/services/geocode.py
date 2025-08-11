from __future__ import annotations

import logging
import requests
from typing import Optional

# תיקון ה-import: הקונפיג יושב תחת core
from ..core.config import settings

log = logging.getLogger("geocode")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def geocode_il(address: str) -> Optional[tuple[float, float]]:
    """
    גיאוקוד כתובת בישראל באמצעות Nominatim.
    מחזיר (lat, lon) או None אם לא נמצא.
    """
    try:
        params = {
            "q": f"{address}, Israel",
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
        }
        # ציין User-Agent תקין כדי להימנע מחסימות
        headers = {"User-Agent": "Zufar/1.0 (contact: admin@example.com)"}
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            log.warning("geocode: no results for address=%s", address)
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)
    except Exception as e:
        log.exception("geocode failed for address=%s: %s", address, e)
        return None
