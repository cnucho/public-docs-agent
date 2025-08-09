from typing import Any, Dict
from .base import Provider
from core.config import KOSIS_API_KEY
from core.errors import fail
from core.http import get, json_safe

class KOSIS(Provider):
    name = "kosis-real"
    BASE = "http://kosis.kr/openapi/Param/statisticsParameterData.do"

    def _key(self):
        if not KOSIS_API_KEY:
            fail("E_NO_KEY","KOSIS_API_KEY 없음", status=500)
        return KOSIS_API_KEY

    def search(self, keyword: str, limit: int = 10, **_)->Dict[str,Any]:
        r = get(self.BASE, params={"method":"getStatList","apiKey":self._key(),"format":"json","keyword":keyword})
        if not r.ok:
            fail("E_HTTP", "KOSIS 검색 실패", {"status": r.status_code, "raw": r.text}, 502)
        data = json_safe(r.text)
        if not isinstance(data, list):
            return {"ok": True, "count": 0, "results": []}
        results = [{
          "idx": i, "ORG_ID": it.get("ORG_ID"), "TBL_ID": it.get("TBL_ID"),
          "TBL_NM": it.get("TBL_NM"), "ORG_NM": it.get("ORG_NM"),
          "LAST_PRD_DE": it.get("LAST_PRD_DE")
        } for i,it in enumerate(data[:limit])]
        return {"ok": True, "count": len(results), "results": results}

    def fetch(self, orgId: str, tblId: str, prdSe="Y", startPrdDe="2020", endPrdDe="2020",
              objL1=None, objL2=None, itmId=None, **_) -> Dict[str,Any]:
        base = {"method":"getList","apiKey":self._key(),"orgId":orgId,"tblId":tblId,
                "prdSe":prdSe,"startPrdDe":startPrdDe,"endPrdDe":endPrdDe,"format":"json"}

        trials = [
            {**base, **({} if objL1 is None else {"objL1":objL1}), **({} if objL2 is None else {"objL2":objL2}), **({} if itmId is None else {"itmId":itmId})},
            {**base, "objL1":"ALL","itmId":"ALL"},
            {**base, "objL1":"0","objL2":"0","itmId":"T1"},
        ]
        last = None
        for p in trials:
            r = get(self.BASE, params=p)
            last = r
            raw = r.text
            if r.ok and "{err:" not in raw:
                data = json_safe(raw)
                preview = data[:3] if isinstance(data, list) else data
                return {"ok": True, "count": (len(data) if isinstance(data,list) else None), "data_preview": preview, "url": r.url}
        fail("E_KOSIS", "KOSIS 조회 실패", {"attempts":[{"url":getattr(last,'url',None),"raw":getattr(last,'text','')[:180]}]}, 502)