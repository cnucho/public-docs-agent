from . import kosis  # 반드시 app/providers/kosis.py 있어야 함

def get_provider(name: str):
    return kosis  # 함수 말고 모듈 반환
