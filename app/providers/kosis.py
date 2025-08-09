# app/providers/kosis.py
# 최소 동작용 스텁. 나중에 실제 KOSIS API 호출로 교체 가능.

from typing import Dict, Any, List, Optional

def search(q: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
    """/agency/search에서 호출. q는 검색어."""
    items: List[Dict[str, Any]] = [
        {"id": "demo-1", "title": f"[예시] {q} 관련 지표 1", "url": "https://kosis.kr"},
        {"id": "demo-2", "title": f"[예시] {q} 관련 지표 2", "url": "https://kosis.kr"},
    ][:limit]
    return {"ok": True, "source": "kosis", "count": len(items), "items": items}

def fetch(id: Optional[str] = None, url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """/agency/fetch에서 호출. id 또는 url을 받는다고 가정."""
    return {
        "ok": True,
        "source": "kosis",
        "id": id or "demo-1",
        "url": url or "https://kosis.kr",
        "title": "샘플 상세 결과",
        "content": "이곳에 실제 KOSIS 응답 파싱 내용을 넣으면 됩니다.",
    }
