# app/providers/registry.py
# 각 기관별 프로바이더 모듈을 임포트
from . import kosis  # kosis.py가 app/providers/ 에 있어야 함

PROVIDERS = {
    "kosis": kosis,
    # 필요해지면 아래에 계속 추가: "law": law, "nkis": nkis
}

def get_provider(name: str):
    key = (name or "").lower().strip()
    if key not in PROVIDERS:
        raise ValueError(f"Unsupported agency: {name}")
    return PROVIDERS[key]

