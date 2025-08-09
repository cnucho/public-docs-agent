from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import os, urllib.parse, requests

app = FastAPI()

# === 기존 라우트나 미들웨어 등이 여기 올 수 있음 ===
# app.add_middleware(...)
# @app.get("/") ...

# === GPT가 만든 KOSIS URL을 받아, 서버 키 붙여 호출하는 프록시 ===
KOSIS_BASE = os.getenv("KOSIS_BASE", "https://kosis.kr/openapi").rstrip("/")
KOSIS_KEY  = os.getenv("KOSIS_API_KEY", "")

def _assert_kosis_url(u: str):
    ok_prefixes = (KOSIS_BASE, "https://kosis.kr/openapi", "http://kosis.kr/openapi")
    if not any(u.startswith(p) for p in ok_prefixes):
        raise HTTPException(status_code=400, detail={"ok": False, "code": "E_URL_DENY", "message": "only kosis.kr/openapi allowed"})

@app.get("/proxy/kosis")
def proxy_kosis(url: str = Query(..., description="apiKey 없이 만든 KOSIS URL")):
    if not KOSIS_KEY:
        raise HTTPException(status_code=400, detail={"ok": False, "code": "E_NO_KEY", "message": "KOSIS_API_KEY not set"})

    url = url.strip()
    _assert_kosis_url(url)

    parsed = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    # 전달된 키 제거 후 서버 키 부착
    q = [(k, v) for (k, v) in q if k.lower() not in ("apikey", "servicekey")]
    q.append(("apiKey", KOSIS_KEY))

    target = urllib.parse.urlunsplit((
        parsed.scheme, parsed.netloc, parsed.path,
        urllib.parse.urlencode(q, doseq=True),
        parsed.fragment
    ))

    try:
        r = requests.get(target, timeout=20, allow_redirects=False)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail={"ok": False, "code": "E_UPSTREAM", "message": str(e)})

    ct = (r.headers.get("content-type") or "").lower()
    content = r.json() if "json" in ct else r.text
    return JSONResponse(status_code=r.status_code, content={
        "ok": r.status_code == 200,
        "source_url": target,  # 필요시 마스킹 가능
        "data": content,
    })

