import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from .config import settings


def duckduckgo_search(query: str, max_results: int = 10) -> List[Dict]:
    url = "https://duckduckgo.com/html/"
    params = {"q": query, "kh": "1", "kp": "-1"}
    try:
        r = requests.get(url,
                         params=params,
                         timeout=15,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.select("a.result__a"):
        title = a.get_text(strip=True)
        href = a.get("href")
        result_div = a.find_parent("div", class_="result")
        snippet_tag = result_div.select_one(
            ".result__snippet") if result_div else None
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def serper_search(query: str, max_results: int = 8) -> List[Dict]:
    if not settings.serper_api_key:
        return []
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json"
    }
    payload = {"q": query, "num": max_results, "gl": "cn", "hl": "zh-cn"}
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet")
        })
    return results


def search_finance(query: str, max_results: int = 8) -> List[Dict]:
    provider = settings.search_provider.lower()
    # 优先使用Serper（需SERPER_API_KEY）
    if settings.serper_api_key:
        return serper_search(query, max_results)
    if provider == "duckduckgo":
        return duckduckgo_search(query, max_results)
    return duckduckgo_search(query, max_results)
