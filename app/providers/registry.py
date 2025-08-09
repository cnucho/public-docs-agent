# app/providers/registry.py
from typing import Callable

MODES = ["default"]

def get_provider(name: str) -> Callable:
    # 임시 no-op 프로바이더 (입력 그대로 반환)
    return lambda x: x
