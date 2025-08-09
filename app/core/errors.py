from fastapi import HTTPException

def fail(code: str, message: str, detail=None, status=400):
    payload = {"ok": False, "code": code, "message": message}
    if detail is not None:
        payload["detail"] = detail
    raise HTTPException(status_code=status, detail=payload)

def ok(items=None, **kw):
    return {"ok": True, "ver": "1.0", "items": items or [], "next": None, "note": None, **kw}