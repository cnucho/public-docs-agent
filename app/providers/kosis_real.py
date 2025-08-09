# app/providers/kosis_real.py
from __future__ import annotations
import os
import urllib.parse
from typing import Any, Dict
import httpx
from fastapi import HTTPException

# 환경변수
BASE = os.getenv("KOSIS_BASE_URL", "https://kosis.kr/openapi").rstrip("/")
KEY  = os.getenv("KOSIS_API_KEY")
KEY_PARAM = os.getenv("KOSIS_KEY_PARAM", "serviceKey")  # 일부 API는 apiKey
TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))

if not KEY:
    # registry에서 mock으로 빠지도록 하는 게 이상적이나, 여기서 명확히 에러
    raise HTTPException(status_code=500, detail="KOSIS_API_KEY 누락")

ENC_KEY = urllib.parse.quote(KEY, safe="")  # 1회만 인코딩

class KosisRealProvider:
    """KOSIS 실사용 프로바이더"""

    name = "kosis-real"

    def __init__(self) -> None:
        self.base = BASE
        self.key_param = KEY_PARAM

    def _get(self, path: str, params: Dict[str, Any]) -> httpx.Response:
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base}{path}"

        q = dict(params or {})
        # 중복 방지
        q.pop("serviceKey", None)
        q.pop("apiKey", None)
        q[self.key_param] = ENC_KEY

        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, params=q)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail={
                "url": str(r.url),
                "status": r.status_code,
                "text": r.text[:500],
            })
        return r

    # ── 검색: 엔드포인트가 과제마다 달라서 최소 스텁 제공 ──
    # 필요 시 '/statisticsParameterData.do'로 구현 확장
    def search(self, keyword: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        return {
            "ok": True,
            "results": [],
            "note": "search는 프로젝트별 파라미터가 달라 스텁으로 둠. fetch로 실데이터 확인 권장.",
        }

    # ── 페치: 통상 '/statisticsData.do' 사용 ──
    def fetch(self, path: str | None = None, **params) -> Dict[str, Any]:
        # path 미지정 시 기본 본데이터 엔드포인트
        path = path or "/statisticsData.do"
        r = self._get(path, params)
        ct = r.headers.get("content-type", "").lower()
        if "json" in ct:
            data = r.json()
        else:
            # CSV 등은 그대로 텍스트로
            data = r.text
        return {
            "ok": True,
            "data": data,
            "source": str(r.url),
        }

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
