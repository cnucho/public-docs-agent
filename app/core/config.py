import os

APP_NAME = "공공문서 검색 에이전트"
APP_VER = "1.2.0"

LAW_API_KEY   = os.getenv("LAW_API_KEY", "")
KOSIS_API_KEY = os.getenv("KOSIS_API_KEY", "")
NKIS_API_KEY  = os.getenv("NKIS_API_KEY", "")
KOSIS_BASE = os.getenv("KOSIS_BASE", "https://kosis.kr/openapi")

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "12"))
RETRIES = int(os.getenv("HTTP_RETRIES", "1"))
