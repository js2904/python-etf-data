import re
import json
import base64
import requests
from bs4 import BeautifulSoup

SESSION_ID_RE = re.compile(r"WSDOM\.Page\.sessionID\s*=\s*WSOD_DATA\.sessionID\s*\|\|\s*'([^']+)'")
WSOD_ISSUE_RE = re.compile(r"var gSymbolWSODIssue = '(\d+)'")

def parse_num(val):
    val = val.strip().upper().replace(",", "").replace("$", "")
    try:
        if val.endswith("%"):
            return float(val[:-1]) / 100
        if val[-1] in {'B', 'M', 'K'}:
            return float(val[:-1]) * {'B': 1e9, 'M': 1e6, 'K': 1e3}[val[-1]]
        return float(val) if val else 0.0
    except:
        return 0.0  # fallback to 0 if bad format

def parse_holdings(raw):
    txt = raw.strip()
    if txt.startswith("this.apiReturn ="):
        txt = txt[len("this.apiReturn = "):]
    if txt.endswith(";"):
        txt = txt[:-1]

    data = json.loads(txt)
    rows = data["module"]["c"][0]["c"][1]["c"]
    out = []

    for row in rows:
        c = row["c"]
        try:
            out.append({
                "symbol": c[0]["c"][0] if "c" in c[0] else "",
                "name": c[1]["c"][0] if "c" in c[1] else "",
                "weight_pct": parse_num(c[2]["c"][0]),
                "shares": parse_num(c[3]["c"][0]),
                "market_value_usd": parse_num(c[4]["c"][0])
            })
        except:
            pass  # skip bad rows

    return out

def scrape_etf(symbol, nrows):
    url = f"https://www.schwab.wallst.com/schwab/Prospect/research/etfs/schwabETF/index.asp?type=holdings&symbol={symbol}"
    sess = requests.Session()
    resp = sess.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": url})
    resp.raise_for_status()

    sessionid = SESSION_ID_RE.search(resp.text).group(1)
    wsodid = WSOD_ISSUE_RE.search(resp.text).group(1)

    soup = BeautifulSoup(resp.text, "lxml")
    summary = {}

    try:
        tbl = soup.select_one("div.popupVersion.realtime table tr:nth-of-type(2)").find_all("td")
        summary = {
            "last_price": tbl[0].text.strip(),
            "change": tbl[2].text.strip().replace("\n", " "),
            "bid": tbl[4].select_one(".value").text.strip(),
            "bid_size": tbl[4].select_one(".sublabel").text.strip(),
            "ask": tbl[6].select_one(".value").text.strip(),
            "ask_size": tbl[6].select_one(".sublabel").text.strip(),
            "volume": tbl[8].select_one(".value").text.strip(),
            "volume_label": tbl[8].select_one(".sublabel").text.strip(),
            "as_of": soup.select_one("#firstGlanceFooter").text.replace("As of", "").strip()
        }
    except:
        print("[x] summary parse fail")

    try:
        summary["title"] = soup.select_one("#content > div > h2").text.strip()
    except:
        print("[x] title parse fail")

    api = f"https://www.schwab.wallst.com/schwab/Prospect/research/resources/server/Module/SchwabETF.ModuleAPI.asp?{sessionid}"
    mod_args = {
        "ModuleID": "holdingsTableContainer",
        "symbol": symbol,
        "wsodissue": wsodid,
        "sortDir": "desc",
        "sortBy": "PctNetAssets",
        "page": "1",
        "numRows": str(nrows),
        "isThirdPartyETF": "true"
    }

    payload = {
        "module": "schwabETFHoldingsTable",
        "moduleArgs": mod_args
    }

    enc = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    body = f"inputs=B64ENC{enc}&..contenttype..=text/javascript&..requester..=ContentBuffer"

    post_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": url,
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    }

    r2 = sess.post(api, headers=post_headers, data=body)
    r2.raise_for_status()
    holdings = parse_holdings(r2.text)

    return summary, holdings
