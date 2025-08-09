# app/providers/kosis_mock.py
from typing import Any, Dict
from fastapi import Response

class KosisMockProvider:
    """KOSIS 목업 프로바이더 (키 없을 때/개발용)"""
    name = "kosis-mock"

    def search(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        items = [
            {"id": "DT_DEMO_001", "title": "[KOSIS] 전기차 관련 지표 1", "url": "https://kosis.kr"},
            {"id": "DT_DEMO_002", "title": "[KOSIS] 전기차 관련 지표 2", "url": "https://kosis.kr"},
        ][:max(0, int(limit))]
        return {"ok": True, "results": items}

    def fetch(self, **params) -> Dict[str, Any]:
        preview = [{"colA": 1, "colB": 2}, {"colA": 3, "colB": 4}]
        return {"ok": True, "data_preview": preview, "source": "mock"}
