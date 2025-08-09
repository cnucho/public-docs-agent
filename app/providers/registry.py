import os
from .kosis_real import KosisRealProvider
from .kosis_mock import KosisMockProvider
from .law_mock import LawMockProvider

MODES = {
    "kosis": "real" if os.getenv("KOSIS_API_KEY") else "mock",
    "law":   "mock",
    "nkis":  "mock",
}

def get_provider(name: str):
    n = (name or "").lower()
    if n == "kosis":
        return KosisRealProvider() if MODES["kosis"] == "real" else KosisMockProvider()
    if n == "law":
        return LawMockProvider()
    raise ValueError(f"unknown provider: {name}")

