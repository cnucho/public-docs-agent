# 공공문서 검색 에이전트

국가법령정보센터(law.go.kr)와 KOSIS(kosis.kr) 공식 Open API를 이용하는 검색 API.

## 로컬 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export LAW_API_KEY=당신의_법령_API키
export KOSIS_API_KEY=당신의_KOSIS_API키

uvicorn src.main:app --reload
```

- 문서: http://127.0.0.1:8000/docs
