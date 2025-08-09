# app/providers/registry.py
from . import kosis  # app/providers/kosis.py 있어야 함

MODES = ["default"]

PROVIDERS = {
    "kosis": kosis,  # 반드시 "모듈"을 반환하도록 유지
}

def get_provider(name: str):
    key = (name or "kosis").lower().strip()
    if key not in PROVIDERS:
        raise ValueError(f"Unsupported agency: {name}")
    return PROVIDERS[key]  # 함수가 아니라 모듈
