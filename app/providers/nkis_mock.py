from typing import Any, Dict
from .base import Provider

class NKISMock(Provider):
    name = "nkis-mock"
    def search(self, keyword: str, pageNo:int=1, rowCnt:int=10, **_)->Dict[str,Any]:
        return {"ok": True, "count": 1, "items":[{"OTP_ID":"M1","OTP_SEQ":"1","TITLE":f"[MOCK] {keyword} 정책보고서"}]}
    def fetch(self, otpId:str, otpSeq:str, **_)->Dict[str,Any]:
        return {"ok": True, "data": {"ABSTRACT":"[MOCK] 초록 내용", "PDF_URL":"https://example.com/mock.pdf"}}