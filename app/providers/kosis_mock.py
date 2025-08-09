from typing import Any, Dict
from .base import Provider

class KOSISMock(Provider):
    name = "kosis-mock"
    def search(self, keyword: str, limit: int = 5, **_)->Dict[str,Any]:
        return {"ok": True, "count": 1, "results": [{
            "idx": 0, "ORG_ID": "101", "TBL_ID": "DT_MOCK_001",
            "TBL_NM": f"[MOCK] {keyword} 관련 지표", "ORG_NM": "통계청",
            "LAST_PRD_DE": "2024"
        }]}
    def fetch(self, orgId: str, tblId: str, **_)->Dict[str,Any]:
        return {"ok": True, "count": 3, "data_preview": [
            {"PRD_DE":"2022","C1":"ALL","ITM_ID":"T1","DT":"123.4"},
            {"PRD_DE":"2023","C1":"ALL","ITM_ID":"T1","DT":"125.7"},
            {"PRD_DE":"2024","C1":"ALL","ITM_ID":"T1","DT":"128.0"},
        ]}