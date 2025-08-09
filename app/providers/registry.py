# app/providers/registry.py
from . import kosis  # app/providers/kosis.py 가 있어야 함

PROVIDERS = {
    "kosis": kosis,
}

def get_provider(name: str):
    key = (name or "").lower().strip()
    if key not in PROVIDERS:
        raise ValueError(f"Unsupported agency: {name}")
    return PROVIDERS[key]  # 함수가 아니라 "모듈" 반환
