import os
print("DEBUG  KOSIS_API_KEY:", os.environ.get("KOSIS_API_KEY"))
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from services.law_service import search_law
from services.stat_service import search_stats_userstats, search_stats_table

APP_NAME = "공공문서 검색 에이전트"
APP_DESC = "국가법령정보센터(law.go.kr), KOSIS(kosis.kr) 공식 Open API 기반 검색"
APP_VER = "1.1.0"

app = FastAPI(title=APP_NAME, description=APP_DESC, version=APP_VER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LAW_API_KEY = os.getenv("LAW_API_KEY", "")
KOSIS_API_KEY = os.getenv("KOSIS_API_KEY", "")

@app.get("/")
def home():
    return {
        "message": f"{APP_NAME} API 입니다.",
        "version": APP_VER,
        "endpoints": {
            "/law": "법령 검색",
            "/stats/userstats": "KOSIS 사용자지정통계 조회",
            "/stats/table": "KOSIS 표 조회",
            "/healthz": "상태 점검",
        }
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/law")
def law_endpoint(query: str = Query(...), page: int = Query(1), display: int = Query(10)):
    if not LAW_API_KEY:
        raise HTTPException(500, "환경변수 LAW_API_KEY가 설정되지 않았습니다.")
    return search_law(LAW_API_KEY, query=query, page=page, display=display)

@app.get("/stats/userstats")
def kosis_userstats_endpoint(userStatsId: str = Query(...), start_year: int = Query(...), end_year: int = Query(...)):
    if not KOSIS_API_KEY:
        raise HTTPException(500, "환경변수 KOSIS_API_KEY가 설정되지 않았습니다.")
    return search_stats_userstats(KOSIS_API_KEY, userStatsId, start_year, end_year)

@app.get("/stats/table")
def kosis_table_endpoint(orgId: str = Query(...), tblId: str = Query(...), start_year: int = Query(...), end_year: int = Query(...), prdSe: str = Query("Y"), itmId: str | None = Query(None)):
    if not KOSIS_API_KEY:
        raise HTTPException(500, "환경변수 KOSIS_API_KEY가 설정되지 않았습니다.")
    return search_stats_table(KOSIS_API_KEY, orgId, tblId, start_year, end_year, prdSe, itmId)
@app.get("/check_kosis")
def check_kosis():
    import requests
    api_key = os.environ.get("KOSIS_API_KEY")
    if not api_key:
        return {"ok": False, "error": "환경변수 없음"}

    url = (
        "http://kosis.kr/openapi/Param/statisticsParameterData.do"
        "?method=getList"
        f"&apiKey={api_key}"
        "&itmId=T1"
        "&objL1=0"
        "&objL2=0"
        "&format=json"
        "&prdSe=Y"
        "&startPrdDe=2020"
        "&endPrdDe=2020"
    )

    try:
        r = requests.get(url, timeout=10)
        return {
            "ok": r.ok,
            "status": r.status_code,
            "preview": r.text[:200]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
