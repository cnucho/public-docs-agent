# app/providers/registry.py
import os
from typing import Dict, Any

# ---- 모드 결정 ----
def _kosis_mode() -> str:
    env = (os.getenv("KOSIS_MODE") or "").lower()
    if env in {"real", "mock"}:
        return env
    # fallback: 키 유무로 자동판단
    return "real" if os.getenv("KOSIS_API_KEY") else "mock"

def _law_mode() -> str:
    env = (os.getenv("LAW_MODE") or "").lower()
    return env if env in {"real", "mock"} else "mock"

def _nkis_mode() -> str:
    env = (os.getenv("NKIS_MODE") or "").lower()
    return env if env in {"real", "mock"} else "mock"

def current_modes() -> Dict[str, str]:
    return {
        "kosis": _kosis_mode(),
        "law":   _law_mode(),
        "nkis":  _nkis_mode(),
    }

# 초기 스냅샷(하위호환용). 실시간 값은 current_modes() 사용 권장.
MODES = current_modes()

# ---- 프로바이더 싱글톤 캐시 ----
_SINGLETONS: Dict[str, Any] = {}

def _get_kosis_provider():
    mode = _kosis_mode()
    if mode == "real":
        if "kosis_real" not in _SINGLETONS:
            from .kosis_real import KosisRealProvider
            _SINGLETONS["kosis_real"] = KosisRealProvider()
        return _SINGLETONS["kosis_real"]
    else:
        if "kosis_mock" not in _SINGLETONS:
            from .kosis_mock import KosisMockProvider
            _SINGLETONS["kosis_mock"] = KosisMockProvider()
        return _SINGLETONS["kosis_mock"]

def _get_law_provider():
    mode = _law_mode()
    if mode == "real":
        # 필요 시 실제 구현 연결
        # from .law_real import LawRealProvider
        # return LawRealProvider()
        pass
    from .law_mock import LawMockProvider
    return LawMockProvider()

def _get_nkis_provider():
    mode = _nkis_mode()
    if mode == "real":
        # 필요 시 실제 구현 연결
        # from .nkis_real import NkisRealProvider
        # return NkisRealProvider()
        pass
    from .nkis_mock import NkisMockProvider
    return NkisMockProvider()

# ---- 공개 API ----
def get_provider(name: str):
    n = (name or "").lower()
    if n == "kosis":
        return _get_kosis_provider()
    if n == "law":
        return _get_law_provider()
    if n == "nkis":
        return _get_nkis_provider()
    raise ValueError(f"unknown provider: {name}")



