# 공공문서 검색 에이전트 (FastAPI)

기관별 Open API(KOSIS, 법제처, NKIS 등)를 **Provider 패턴**으로 묶고, 키가 없어도 **Mock**으로 동작하며,
실패 시 **자동 폴백**(옵션)을 제공하는 서버입니다. GPT/웹프런트가 소비하기 쉬운 **표준 JSON 스키마**를 반환합니다.

## 특징
- `search / fetch` **고정 인터페이스**
- `AGENCY_MODE_*` (auto|real|mock) **모드 스위치**
- `ALLOW_FALLBACK=1` 시 **실패 → mock 폴백**
- `/admin/status`, `/admin/selftest` **운영 헬스 확인**
- 표준 응답 스키마(`ok, code, message, items, next, note, source`)

## 엔드포인트 요약
- `GET /` : 인덱스
- `GET /healthz` : 라이브니스
- `GET /admin/status` : 현재 모드/키 설정 확인
- `GET /admin/selftest?agency={kosis|law|nkis}` : 간단 스모크 테스트
- `GET /agency/search?agency=kosis&q=실업률&limit=5`
- `GET /agency/fetch?agency=kosis&orgId=...&tblId=...`

## 환경변수
- `KOSIS_API_KEY` (있으면 real, 없으면 mock)
- `LAW_API_KEY` (향후 real 구현 시 사용)
- `NKIS_API_KEY` (향후 real 구현 시 사용)
- `AGENCY_MODE_KOSIS`=`auto|real|mock` (기본 `auto`)
- `AGENCY_MODE_LAW`=`auto|real|mock` (기본 `auto`)
- `AGENCY_MODE_NKIS`=`auto|real|mock` (기본 `auto`)
- `ALLOW_FALLBACK`=`1|0` (기본 `1`)

## 로컬 실행
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Render 배포
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Build Command 없음(자동). 환경변수 저장 후 **Redeploy**.

## 표준 응답 스키마
성공:
```json
{ "ok": true, "provider": "kosis-real", "ver": "1.0",
  "query": {"agency":"kosis","q":"실업률"},
  "count": 10, "next": null, "items": [ ... ],
  "note": null, "source": [{"name":"KOSIS","url":"http://kosis.kr/"}]
}
```
실패:
```json
{ "ok": false, "code": "E_KOSIS", "message": "필수요청변수 누락",
  "detail": {"hint": "itmId 필요", "url": "http://kosis.kr/..."} }
```

## 라이선스
MIT