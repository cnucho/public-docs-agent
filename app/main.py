from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core import config
from app.core.errors import ok, fail
from .providers.registry import get_provider, MODES

app = FastAPI(title=config.APP_NAME, version=config.APP_VER, description="공공문서 통합 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.exception_handler(Exception)
async def all_errors(request: Request, exc: Exception):
    if hasattr(exc, "status_code"):
        # HTTPException → detail에 이미 통일 포맷
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=500, content={"ok": False, "code": "E_INTERNAL", "message": str(exc)})

@app.get("/")
def home():
    return {
        "message": f"{config.APP_NAME} API 입니다.",
        "version": config.APP_VER,
        "endpoints": {
            "/agency/search": "기관별 검색",
            "/agency/fetch":  "기관별 상세/데이터",
            "/healthz": "상태 점검",
            "/admin/status": "현재 어댑터/키 상태",
            "/admin/selftest": "간단 스모크테스트",
            "/health": "헬스체크",
            "/diag/env": "환경변수 확인",
        }
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

from app.providers.registry import get_provider, MODES

@app.get("/admin/status")
def admin_status():
    from app.core import config
    return {
        "modes": MODES,
        "keys": {
            "KOSIS_API_KEY": bool(config.KOSIS_API_KEY),
            "LAW_API_KEY":   bool(config.LAW_API_KEY),
            "NKIS_API_KEY":  bool(config.NKIS_API_KEY),
        }
    }


@app.get("/admin/selftest")
def admin_selftest(agency: str):
    p = get_provider(agency)
    if not p:
        return {"ok": False, "message": "no such agency"}
    try:
        if agency.lower() == "kosis":
            s = p.search(keyword="전기차")
            f = p.fetch(orgId="101", tblId="DT_MOCK_001")
        elif agency.lower() == "law":
            s = p.search(query="전기차")
            f = p.fetch()
        else:
            s = p.search(keyword="전기차")
            f = p.fetch(otpId="M1", otpSeq="1")
        return {
            "ok": bool(s.get("ok")),
            "search_ok": s.get("ok"),
            "fetch_ok": (f or {}).get("ok", None),
            "provider": getattr(p, "name", "?"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "provider": getattr(p, "name", "?")}

@app.get("/agency/search")
def agency_search(
    agency: str = Query(...),
    q: str = Query(...),
    limit: int = 10,
    cursor: str | None = None,
    sort: str | None = None
):
    p = get_provider(agency)
    if not p:
        return fail("E_NO_AGENCY", f"지원하지 않는 기관: {agency}")

    if agency.lower() == "kosis":
        res = p.search(keyword=q, limit=limit)
    elif agency.lower() == "law":
        res = p.search(query=q, page=1, display=limit)
    elif agency.lower() == "nkis":
        res = p.search(keyword=q, pageNo=1, rowCnt=limit)
    else:
        return fail("E_ROUTE", "라우팅 실패")

    if not res.get("ok"):
        return res
    items = res.get("results") or res.get("data") or res.get("items") or []
    return ok(provider=getattr(p, "name", "?"),
              query={"agency": agency, "q": q, "limit": limit},
              count=len(items), items=items)

from fastapi import Request, Query
from app.core.errors import ok, fail
from .providers.registry import get_provider

@app.get("/agency/fetch")
def agency_fetch(agency: str = Query(...), request: Request = None):
    p = get_provider(agency)
    if not p:
        return fail("E_NO_AGENCY", f"지원하지 않는 기관: {agency}")

    q = dict(request.query_params)   # 전체 쿼리 받기
    q.pop("agency", None)            # agency만 제거

    res = p.fetch(**q)               # 키는 서버에서 자동 주입
    if not res.get("ok"):
        return res
    items = res.get("data_preview") or res.get("items") or res.get("data") or []
    return ok(provider=getattr(p, "name", "?"),
              query={"agency": agency, **q},
              items=items, source=res.get("source"))


# ===== 아래 두 엔드포인트는 반드시 최상위(왼쪽 정렬) =====
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/diag/env")
def diag_env():
    import os
    return {"KOSIS_API_KEY_set": bool(os.getenv("KOSIS_API_KEY"))}

from fastapi import Request, Query
import os, urllib.parse, requests
from fastapi.responses import JSONResponse

BASE = "https://kosis.kr/openapi"
KEY  = os.getenv("KOSIS_API_KEY")

def _kosis_get(path, params):
    p = {"format":"json","jsonVD":"Y", **params}
    p.pop("apiKey", None); p.pop("serviceKey", None)
    p["apiKey"] = KEY  # 공식 파라미터명
    url = BASE + (path if path.startswith("/") else "/" + path)
    r = requests.get(url, params=p, timeout=20)
    return JSONResponse(status_code=r.status_code, content=r.json() if "json" in r.headers.get("content-type","").lower() else r.text)

@app.get("/kosis/parameter")
def kosis_parameter(orgId: str = Query(...), tblId: str = Query(...), request: Request = None):
    q = dict(request.query_params); q.pop("orgId", None); q.pop("tblId", None)
    return _kosis_get("/Param/statisticsParameterData.do", {"method":"getList","orgId":orgId,"tblId":tblId, **q})

@app.get("/kosis/data")
def kosis_data(orgId: str = Query(...), tblId: str = Query(...), request: Request = None):
    q = dict(request.query_params); q.pop("orgId", None); q.pop("tblId", None)
    return _kosis_get("/statisticsData.do", {"method":"getList","orgId":orgId,"tblId":tblId, **q})
