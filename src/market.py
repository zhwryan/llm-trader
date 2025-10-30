import requests
from typing import Dict, Any, Optional


def _yf_available():
    try:
        import yfinance as yf
        return yf
    except Exception:
        return None


def _yahoo_quote(symbol: str) -> Optional[Dict[str, Any]]:
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        r = requests.get(url,
                         timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        result = r.json()["quoteResponse"]["result"]
        if not result:
            return None
        q = result[0]
        return {
            "symbol": q.get("symbol"),
            "name": q.get("longName") or q.get("shortName"),
            "currency": q.get("currency"),
            "price": q.get("regularMarketPrice"),
            "change": q.get("regularMarketChange"),
            "changePercent": q.get("regularMarketChangePercent"),
            "marketTime": q.get("regularMarketTime"),
        }
    except Exception:
        return None


def a_symbol_to_yf(code: str) -> str:
    code = code.strip()
    if code.startswith(("6", "9")):
        return f"{code}.SS"  # 上证
    else:
        return f"{code}.SZ"  # 深证


def hk_symbol_to_yf(code: str) -> str:
    code = code.strip()
    try:
        if int(code) < 1000:
            code = code.zfill(4)
    except Exception:
        pass
    return f"{code}.HK"


def _sina_quote(symbol: str, market: str):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn"
    }
    try:
        if market.upper() == "A":
            pref = "sh" if symbol.strip().startswith(("6", "9")) else "sz"
            url = f"https://hq.sinajs.cn/list={pref}{symbol.strip()}"
        elif market.upper() == "HK":
            code = symbol.strip()
            try:
                if int(code) < 10000:
                    code = code.zfill(5)
            except Exception:
                pass
            url = f"https://hq.sinajs.cn/list=hk{code}"
        else:
            return None
        r = requests.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        text = r.text
        if "hq_str" not in text:
            return None
        payload = text.split("=", 1)[1].strip().strip('";')
        parts = payload.split(",")
        if not parts or parts[0] == "":
            return None
        name = parts[0]
        price = None
        if market.upper() == "A":
            if len(parts) > 3 and parts[3]:
                try:
                    price = float(parts[3])
                except Exception:
                    price = None
        else:
            # 新浪港股返回字段中，最新价通常在索引6
            idx = 6 if len(parts) > 6 else 1
            if len(parts) > idx and parts[idx]:
                try:
                    price = float(parts[idx])
                except Exception:
                    price = None
        return {
            "symbol": symbol,
            "name": name,
            "currency": "",
            "price": price,
            "change": None,
            "changePercent": None
        }
    except Exception:
        return None


def get_quote(symbol: str, market: str) -> Dict[str, Any]:
    yf = _yf_available()
    m = market.upper()
    yf_symbol = symbol
    if m == "A":
        yf_symbol = a_symbol_to_yf(symbol)
    elif m == "HK":
        yf_symbol = hk_symbol_to_yf(symbol)

    if yf:
        try:
            ticker = yf.Ticker(yf_symbol)
            info = getattr(ticker, "fast_info", {})
            data = {
                "symbol": yf_symbol,
                "name": "",  # 避免info慢加载
                "currency": info.get("currency", ""),
                "price": info.get("lastPrice"),
                "change": info.get("regularMarketChange"),
                "changePercent": info.get("regularMarketChangePercent"),
                "marketTime": None,
            }
            if data["price"] is None:
                yq = _yahoo_quote(yf_symbol)
                if yq:
                    return yq
            return data
        except Exception:
            pass
    data = _yahoo_quote(yf_symbol)
    if data:
        return data
    sina = _sina_quote(symbol, market)
    if sina:
        return sina
    return {
        "symbol": yf_symbol,
        "name": "",
        "currency": "",
        "price": None,
        "change": None,
        "changePercent": None
    }


def get_history(symbol: str,
                market: str,
                period: str = "1y",
                interval: str = "1d"):
    yf = _yf_available()
    yf_symbol = symbol
    m = market.upper()
    if m == "A":
        yf_symbol = a_symbol_to_yf(symbol)
    elif m == "HK":
        yf_symbol = hk_symbol_to_yf(symbol)
    if yf:
        try:
            return yf.Ticker(yf_symbol).history(period=period,
                                                interval=interval)
        except Exception:
            return None
    return None
