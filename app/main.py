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

@app.api_route("/", methods=["GET", "HEAD"])
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
@app.api_route("/healthz", methods=["GET", "HEAD"])
def healthz():
    return {"ok": True}

# 이미 상단에서: from .providers.registry import get_provider, MODES
# (또는 프로젝트 구조에 맞게 app.providers...로 일관)

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

# --- GET /search: KOSIS 실검색 ---
import requests
from fastapi import HTTPException, Query
from app.core import config
from app.core.errors import ok

@app.get("/search")
def search(
    agency: str = Query(...),
    q: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    if agency.lower() != "kosis":
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "code": "E_ONLY_KOSIS", "message": "agency=kosis 만 지원"}
        )

    import os
    BASE = getattr(config, "KOSIS_BASE", os.getenv("KOSIS_BASE", "https://kosis.kr/openapi"))
    API_KEY = getattr(config, "KOSIS_API_KEY", os.getenv("KOSIS_API_KEY", "")) or ""
    if not API_KEY:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "code": "E_NO_KEY", "message": "KOSIS_API_KEY not set"}
        )

    url = f"{BASE.rstrip('/')}/statisticsSearch.do"
    start = (page - 1) * limit + 1  # 1-base

    params = {
        "method": "getList",
        "apiKey": API_KEY,
        "searchNm": q,
        "format": "json",
        "startCount": start,
        "resultCount": limit
    }

    try:
        r = requests.get(url, params=params, timeout=20, allow_redirects=False)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "code": "E_UPSTREAM", "message": str(e)}
        )

    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "code": "E_UPSTREAM_STATUS", "message": f"{r.status_code} {r.text[:200]}"}
        )

    ct = (r.headers.get("content-type") or "").lower()
    body = r.text
    data = None

    if "json" in ct:
        try:
            data = r.json()
        except ValueError:
            data = None

    if data is None:
        import re, json
        m = re.search(r'\{[^{}]*"err"[^{}]*\}', body)
        if m:
            err_obj = json.loads(m.group(0))
            raise HTTPException(
                status_code=400,
                detail={"ok": False, "code": f"KOSIS_{err_obj.get('err')}", "message": err_obj.get("errMsg")}
            )
        js_like = re.sub(r'([{,]\s*)([A-Z0-9_]+)\s*:', r'\1"\2":', body)
        try:
            data = json.loads(js_like)
        except Exception:
            raise HTTPException(
                status_code=502,
                detail={"ok": False, "code": "E_BAD_JSON", "message": body[:300]}
            )

    if isinstance(data, dict) and "err" in data:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "code": f"KOSIS_{data.get('err')}", "message": data.get("errMsg")}
        )

    items = data if isinstance(data, list) else []
    return ok(
        provider="kosis-real",
        query={"agency": agency, "q": q, "limit": limit, "page": page, "startCount": start},
        count=len(items),
        items=items
    )


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
# --- GET /search: KOSIS 실검색 전용 ---
import os, requests
from fastapi import HTTPException, Query
from app.core import config
from app.core.errors import ok

@app.get("/search")
def search(
    agency: str = Query(...),
    q: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    if agency.lower() != "kosis":
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "code": "E_ONLY_KOSIS", "message": "agency=kosis 만 지원"}
        )

    url = f"{config.KOSIS_BASE.rstrip('/')}/statisticsSearch.do"
    start = (page - 1) * limit + 1  # 1-base

    params = {
        "method": "getList",
        "apiKey": config.KOSIS_API_KEY,
        "searchNm": q,
        "format": "json",
        "startCount": start,
        "resultCount": limit,
        # "sort": "RANK",  # 필요 시
        # "orgId": "101",  # 필요 시
    }

    try:
        r = requests.get(url, params=params, timeout=20, allow_redirects=False)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "code": "E_UPSTREAM", "message": str(e)}
        )

    # 1) HTTP 상태 코드 확인
    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={"ok": False, "code": "E_UPSTREAM_STATUS", "message": f"{r.status_code} {r.text[:200]}"}
        )

    ct = (r.headers.get("content-type") or "").lower()
    body = r.text

    # 2) 먼저 JSON 시도
    data = None
    if "json" in ct:
        try:
            data = r.json()
        except ValueError:
            data = None

    # 3) JSON 실패 시: 에러 JSON 추출 시도
    if data is None:
        import re, json
        m = re.search(r'\{[^{}]*"err"[^{}]*\}', body)
        if m:
            err_obj = json.loads(m.group(0))
            raise HTTPException(
                status_code=400,
                detail={"ok": False, "code": f"KOSIS_{err_obj.get('err')}", "message": err_obj.get("errMsg")}
            )

        js_like = re.sub(r'([{,]\s*)([A-Z0-9_]+)\s*:', r'\1"\2":', body)
        try:
            data = json.loads(js_like)
        except Exception:
            raise HTTPException(
                status_code=502,
                detail={"ok": False, "code": "E_BAD_JSON", "message": body[:300]}
            )

    # 5) KOSIS 에러 포맷 정식 처리
    if isinstance(data, dict) and "err" in data:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "code": f"KOSIS_{data.get('err')}", "message": data.get("errMsg")}
        )

    items = data if isinstance(data, list) else []
    return ok(
        provider="kosis-real",
        query={"agency": agency, "q": q, "limit": limit, "page": page, "startCount": start},
        count=len(items),
        items=items
    )

