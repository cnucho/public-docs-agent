from typing import Any, Dict
from .base import Provider

class LawMock(Provider):
    name = "law-mock"
    def search(self, query: str, page: int=1, display: int=10, **_)->Dict[str,Any]:
        return {"ok": True, "data": {"list":[{"법령명":"[MOCK] 전기차 보조금법","법령ID":"MOCK-1"}]} }
    def fetch(self, **kwargs)->Dict[str,Any]:
        return {"ok": True, "data": {"조문":"[MOCK] 제1조 목적 ..."}}