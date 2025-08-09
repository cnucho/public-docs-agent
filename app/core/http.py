import json, re, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import HTTP_TIMEOUT, RETRIES

_session = requests.Session()
retries = Retry(total=RETRIES, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
_session.mount("http://", HTTPAdapter(max_retries=retries))
_session.mount("https://", HTTPAdapter(max_retries=retries))
_session.headers.update({"User-Agent": "PolicyAgent/1.0"})

def get(url, params=None, timeout=HTTP_TIMEOUT):
    return _session.get(url, params=params, timeout=timeout)

def json_safe(text: str):
    try:
        return json.loads(text)
    except Exception:
        # {KEY:...} → {"KEY":...}
        fixed = re.sub(r'([{,])(\s*)([A-Za-z0-9_]+):', r'\1"\3":', text)
        return json.loads(fixed)