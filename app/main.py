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
        }
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/admin/status")
def admin_status():
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
    if not p: return {"ok": False, "message": "no such agency"}
    try:
        if agency.lower()=="kosis":
            s = p.search(keyword="전기차")
            f = p.fetch(orgId="101", tblId="DT_MOCK_001")
        elif agency.lower()=="law":
            s = p.search(query="전기차")
            f = p.fetch()
        else:
            s = p.search(keyword="전기차")
            f = p.fetch(otpId="M1", otpSeq="1")
        return {"ok": bool(s.get("ok")), "search_ok": s.get("ok"), "fetch_ok": (f or {}).get("ok", None), "provider": getattr(p,"name","?")}
    except Exception as e:
        return {"ok": False, "error": str(e), "provider": getattr(p,"name","?")}

@app.get("/agency/search")
def agency_search(agency: str = Query(...), q: str = Query(...), limit: int = 10, cursor: str | None = None, sort: str | None = None):
    p = get_provider(agency)
    if not p: return fail("E_NO_AGENCY", f"지원하지 않는 기관: {agency}")
    if agency.lower()=="kosis":
        res = p.search(keyword=q, limit=limit)
    elif agency.lower()=="law":
        res = p.search(query=q, page=1, display=limit)
    elif agency.lower()=="nkis":
        res = p.search(keyword=q, pageNo=1, rowCnt=limit)
    else:
        return fail("E_ROUTE", "라우팅 실패")

    if not res.get("ok"): return res
    items = res.get("results") or res.get("data") or res.get("items") or []
    return ok(provider=getattr(p,"name","?"), query={"agency":agency,"q":q,"limit":limit}, count=len(items), items=items)

@app.get("/agency/fetch")
def agency_fetch(agency: str = Query(...), **params):
    p = get_provider(agency)
    if not p: return fail("E_NO_AGENCY", f"지원하지 않는 기관: {agency}")
    res = p.fetch(**params)
    if not res.get("ok"): return res
    items = res.get("data_preview") or res.get("items") or res.get("data") or []
    return ok(provider=getattr(p,"name","?"), query={"agency":agency, **params}, items=items, source=res.get("source"))
    @app.get("/health")
def health(): return {"ok": True}

@app.get("/diag/env")
def diag_env():
    import os
    return {"KOSIS_API_KEY_set": bool(os.getenv("KOSIS_API_KEY"))}
