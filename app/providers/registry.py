# app/providers/registry.py
import os

def _kosis_mode() -> str:
    return "real" if os.getenv("KOSIS_API_KEY") else "mock"

MODES = {
    "kosis": _kosis_mode(),
    "law":   "mock",
    "nkis":  "mock",
}

def get_provider(name: str):
    n = (name or "").lower()
    if n == "kosis":
        if MODES["kosis"] == "real":
            from .kosis_real import KosisRealProvider
            return KosisRealProvider()
        else:
            from .kosis_mock import KosisMockProvider
            return KosisMockProvider()
    if n == "law":
        from .law_mock import LawMockProvider
        return LawMockProvider()
    raise ValueError(f"unknown provider: {name}")


