# app/providers/kosis.py
# main.py에서 p.search(keyword=...), p.fetch(**params)로 호출하므로 여기에 맞춰 구현

name = "kosis"

def search(keyword: str, limit: int = 10, **kwargs):
    # 최소 동작용 모의응답. 실제 API 연동은 추후 교체.
    items = [
        {"id": "DT_DEMO_001", "title": f"[KOSIS] {keyword} 관련 지표 1", "url": "https://kosis.kr"},
        {"id": "DT_DEMO_002", "title": f"[KOSIS] {keyword} 관련 지표 2", "url": "https://kosis.kr"},
    ][:limit]
    return {"ok": True, "results": items}

def fetch(**params):
    # orgId, tblId 등 어떤 키가 와도 에러 없이 통과
    return {
        "ok": True,
        "data_preview": [
            {"col": "예시열1", "val": 123},
            {"col": "예시열2", "val": 456},
        ],
        "echo": params,  # 무엇이 왔는지 확인용
    }
