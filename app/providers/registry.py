# app/providers/registry.py
from types import SimpleNamespace

# kosis 모듈(있으면) 임포트 시도
try:
    from . import kosis  # app/providers/kosis.py
except Exception:
    kosis = None

PROVIDERS = {}
if kosis is not None:
    PROVIDERS["kosis"] = kosis

def _wrap_if_function(obj):
    # 과거 코드가 함수(람다)를 리턴했다면 .search가 없어 AttributeError가 났음
    # 함수라면 .search 속성을 가진 어댑터로 감싸서 호환되게 만든다.
    if callable(obj):
        return SimpleNamespace(search=obj, fetch=lambda **kwargs: {"ok": True, "note": "mock fetch"})
    return obj

def get_provider(name: str):
    key = (name or "").lower().strip()
    if key not in PROVIDERS:
        raise ValueError(f"Unsupported agency: {name}")
    return _wrap_if_function(PROVIDERS[key])
