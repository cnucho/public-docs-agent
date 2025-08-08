import requests

USERSTATS_URL = "https://kosis.kr/openapi/statisticsData.do"

def search_stats_userstats(api_key: str, user_stats_id: str, start_year: int, end_year: int):
    params = {
        "method": "getList",
        "apiKey": api_key,
        "format": "json",
        "jsonVD": "Y",
        "userStatsId": user_stats_id,
        "prdSe": "Y",
        "startPrdDe": start_year,
        "endPrdDe": end_year
    }
    resp = requests.get(USERSTATS_URL, params=params, timeout=20)
    resp.raise_for_status()
    return {"userStatsId": user_stats_id, "period": {"start": start_year, "end": end_year}, "data": resp.json()}

def search_stats_table(api_key: str, orgId: str, tblId: str, start_year: int, end_year: int, prdSe: str = "Y", itmId: str | None = None):
    params = {
        "method": "getList",
        "apiKey": api_key,
        "format": "json",
        "jsonVD": "Y",
        "orgId": orgId,
        "tblId": tblId,
        "prdSe": prdSe,
        "startPrdDe": start_year,
        "endPrdDe": end_year
    }
    if itmId:
        params["itmId"] = itmId
    resp = requests.get(USERSTATS_URL, params=params, timeout=20)
    resp.raise_for_status()
    return {"orgId": orgId, "tblId": tblId, "period": {"start": start_year, "end": end_year, "prdSe": prdSe}, "data": resp.json()}
