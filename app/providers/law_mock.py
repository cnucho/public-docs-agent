# app/providers/law_mock.py
from typing import Any, Dict

class LawMockProvider:
    """LAW 목업 프로바이더 (키/실서비스 없을 때 사용)"""
    name = "law-mock"

    def search(self, query: str, page: int = 1, display: int = 10, **kwargs) -> Dict[str, Any]:
        items = [
            {"id": "LAW_DEMO_001", "title": "[LAW] 전기차 관련 법령 1", "url": "https://www.law.go.kr/"},
            {"id": "LAW_DEMO_002", "title": "[LAW] 전기차 관련 법령 2", "url": "https://www.law.go.kr/"},
        ][:max(0, int(display))]
        return {"ok": True, "results": items}

    def fetch(self, **params) -> Dict[str, Any]:
        # 간단 목업 데이터
        return {"ok": True, "data": {"article": "MOCK_CONTENT"}, "source": "mock"}
