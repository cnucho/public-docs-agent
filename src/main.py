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
@app.get("/kosis")
def kosis(
    orgId: str,
    tblId: str,
    prdSe: str = "Y",
    startPrdDe: str = "2020",
    endPrdDe: str = "2020",
    objL1: str = "0",
    objL2: str = "0",
    itmId: str = "T1"
):
    import os, requests
    api_key = os.environ.get("KOSIS_API_KEY")
    if not api_key:
        return {"ok": False, "error": "환경변수 없음"}

    url = "http://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": api_key,
        "orgId": orgId,
        "tblId": tblId,
        "prdSe": prdSe,
        "startPrdDe": startPrdDe,
        "endPrdDe": endPrdDe,
        "objL1": objL1,
        "objL2": objL2,
        "itmId": itmId,
        "format": "json",
    }
    r = requests.get(url, params=params, timeout=12)
    return {
        "ok": r.ok,
        "status": r.status_code,
        "url": r.url,
        "preview": r.text[:500]
    }
@app.get("/query")
def query_agency(
    agency: str,
    keyword: str,
    startPrdDe: str = "2020",
    endPrdDe: str = "2020",
    prdSe: str = "Y"
):
    import os, requests, json, re
    
    keys = {
        "kosis": os.environ.get("KOSIS_API_KEY"),
    }
    if agency not in keys:
        return {"ok": False, "error": f"지원하지 않는 기관: {agency}"}
    if not keys[agency]:
        return {"ok": False, "error": f"{agency} API 키 없음"}
    api_key = keys[agency]

    def fix_json(text):
        return re.sub(r'([{,])(\s*)([A-Za-z0-9_]+):', r'\1"\3":', text)

    try:
        if agency == "kosis":
            base_url = "http://kosis.kr/openapi/Param/statisticsParameterData.do"
            
            # 1) 검색
            search_params = {
                "method": "getStatList",
                "apiKey": api_key,
                "format": "json",
                "keyword": keyword
            }
            sr = requests.get(base_url, params=search_params, timeout=10)
            raw_text = sr.text
            if not sr.ok:
                return {"ok": False, "status": sr.status_code, "raw": raw_text}

            try:
                tables = sr.json()
            except:
                try:
                    tables = json.loads(fix_json(raw_text))
                except:
                    return {"ok": False, "error": "검색결과 파싱 실패", "raw": raw_text}

            if not isinstance(tables, list) or not tables:
                return {"ok": False, "error": "검색 결과 없음", "raw": tables}

            best = tables[0]
            orgId = best.get("ORG_ID")
            tblId = best.get("TBL_ID")

            # 2) 데이터 조회
            data_params = {
                "method": "getList",
                "apiKey": api_key,
                "orgId": orgId,
                "tblId": tblId,
                "prdSe": prdSe,
                "startPrdDe": startPrdDe,
                "endPrdDe": endPrdDe,
                "format": "json",
                "objL1": "ALL",
                "itmId": "ALL"
            }
            dr = requests.get(base_url, params=data_params, timeout=10)
            data_text = dr.text
            try:
                data_json = dr.json()
            except:
                try:
                    data_json = json.loads(fix_json(data_text))
                except:
                    return {"ok": False, "error": "데이터 파싱 실패", "raw": data_text}

            return {
                "ok": True,
                "selected_table": {
                    "TBL_ID": tblId,
                    "ORG_ID": orgId,
                    "TBL_NM": best.get("TBL_NM"),
                    "ORG_NM": best.get("ORG_NM"),
                },
                "data_count": len(data_json) if isinstance(data_json, list) else None,
                "data_preview": data_json[:3] if isinstance(data_json, list) else data_json
            }

    except Exception as e:
        return {"ok": False, "error": str(e)}
@app.get("/kosis/search")
def kosis_search(keyword: str, limit: int = 10):
    import os, requests, json, re
    api_key = os.environ.get("KOSIS_API_KEY")
    if not api_key:
        return {"ok": False, "error": "KOSIS_API_KEY 없음"}

    def fix_json(text: str) -> str:
        # {KEY: ...} → {"KEY": ...}
        return re.sub(r'([{,])(\s*)([A-Za-z0-9_]+):', r'\1"\3":', text)

    url = "http://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {"method": "getStatList", "apiKey": api_key, "format": "json", "keyword": keyword}
    r = requests.get(url, params=params, timeout=12)
    raw = r.text
    if not r.ok:
        return {"ok": False, "status": r.status_code, "raw": raw}

    try:
        data = r.json()
    except:
        try:
            data = json.loads(fix_json(raw))
        except Exception as e:
            return {"ok": False, "error": f"검색결과 파싱 실패: {e}", "raw": raw}

    if not isinstance(data, list) or not data:
        return {"ok": True, "count": 0, "results": []}

    results = []
    for i, item in enumerate(data[:limit]):
        results.append({
            "idx": i,
            "ORG_ID": item.get("ORG_ID"),
            "TBL_ID": item.get("TBL_ID"),
            "TBL_NM": item.get("TBL_NM"),
            "ORG_NM": item.get("ORG_NM"),
            "LAST_PRD_DE": item.get("LAST_PRD_DE"),
        })
    return {"ok": True, "count": len(results), "results": results}


@app.get("/kosis/fetch")
def kosis_fetch(
    orgId: str,
    tblId: str,
    prdSe: str = "Y",
    startPrdDe: str = "2020",
    endPrdDe: str = "2020",
    objL1: str | None = None,
    objL2: str | None = None,
    itmId: str | None = None,
):
    import os, requests, json, re
    api_key = os.environ.get("KOSIS_API_KEY")
    if not api_key:
        return {"ok": False, "error": "KOSIS_API_KEY 없음"}

    def fix_json(text: str) -> str:
        return re.sub(r'([{,])(\s*)([A-Za-z0-9_]+):', r'\1"\3":', text)

    url = "http://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList",
        "apiKey": api_key,
        "orgId": orgId,
        "tblId": tblId,
        "prdSe": prdSe,
        "startPrdDe": startPrdDe,
        "endPrdDe": endPrdDe,
        "format": "json",
    }
    # 선택값만 붙임(틀린 코드로 21 에러 방지)
    if objL1 is not None: params["objL1"] = objL1
    if objL2 is not None: params["objL2"] = objL2
    if itmId is not None: params["itmId"] = itmId

    r = requests.get(url, params=params, timeout=12)
    raw = r.text
    if '{err:' in raw:
        return {"ok": False, "status": r.status_code, "kosis_error_raw": raw, "url": r.url}

    try:
        data = r.json()
    except:
        try:
            data = json.loads(fix_json(raw))
        except Exception as e:
            return {"ok": False, "error": f"데이터 파싱 실패: {e}", "raw": raw, "url": r.url}

    preview = data[:3] if isinstance(data, list) else data
    return {"ok": True, "count": (len(data) if isinstance(data, list) else None), "data_preview": preview, "url": r.url}


@app.get("/kosis/quick")
def kosis_quick(keyword: str, prdSe: str = "Y", startPrdDe: str = "2020", endPrdDe: str = "2020"):
    """
    1) 검색 → 2) 첫 결과 자동 선택 → 3) fetch 까지 한 번에
    """
    s = kosis_search.__wrapped__   # 데코레이터 우회 호출
    f = kosis_fetch.__wrapped__

    res = s(keyword)
    if not res.get("ok"):
        return res
    if res.get("count", 0) == 0:
        return {"ok": False, "error": "검색 결과 없음", "keyword": keyword}

    top = res["results"][0]
    return f(orgId=top["ORG_ID"], tblId=top["TBL_ID"], prdSe=prdSe, startPrdDe=startPrdDe, endPrdDe=endPrdDe)
