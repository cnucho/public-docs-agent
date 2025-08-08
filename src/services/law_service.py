import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://www.law.go.kr/DRF/lawSearch.do"

def _safe_text(elem, tag):
    found = elem.find(tag)
    return found.text.strip() if (found is not None and found.text) else None

def search_law(api_key: str, query: str, page: int = 1, display: int = 10):
    params = {
        "OC": api_key,
        "target": "law",
        "type": "XML",
        "query": query,
        "page": page,
        "display": display
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    xml_text = resp.text
    parsed_items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.iter():
            if item.tag.lower() in {"law", "row"}:
                parsed_items.append({
                    "law_name": _safe_text(item, "법령명한글"),
                    "law_id": _safe_text(item, "법령ID"),
                    "promulgation_date": _safe_text(item, "공포일자"),
                    "enforcement_date": _safe_text(item, "시행일자"),
                    "detail_url": _safe_text(item, "법령상세링크")
                })
    except Exception:
        parsed_items = []
    return {"query": query, "page": page, "display": display, "count_parsed": len(parsed_items), "items": parsed_items, "raw_xml": xml_text}
