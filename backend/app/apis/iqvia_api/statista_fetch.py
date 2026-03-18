# statista_serp.py
import requests
import uuid

# Hard-coded working cookie jar (from your curl)
STATISTA_COOKIES = {
    "__sso_status": "dHJ1ZQ==",
    "STATSESSID": "711d9e1aff7ea2d89cb26a2b723d63c4",
    "ajs_user_id": "10153501",
    "_ga": "GA1.1.1709527737.1769521644",
    "_ga_2T9EQH2NQC": "GS2.1.s1769521644",
    "OptanonAlertBoxClosed": "true",
    "OptanonConsent": "isGpcEnabled=0",
    # (you can paste full cookie map here once and forget forever)
}


def fetch_statista_search(
    query: str,
    page: int = 1,
    sort: str = "relevance",  # relevance | date
    content_type: str | None = None,  # statistics | infographics | reports
    language: str = "en",
):
    """
    Only parameters that change search output are exposed.
    Transport/session handled internally.
    """

    url = "https://www.statista.com/serp"

    params = {
        "q": query,
        "uuid": str(uuid.uuid4()),
        "_data": "routes/_index",
        "page": page,
        "sort": sort,
        "language": language,
    }

    if content_type:
        params["type"] = content_type

    headers = {
        "user-agent": "Mozilla/5.0",
        "accept": "*/*",
        "referer": f"https://www.statista.com/serp?q={query}",
    }

    response = requests.get(
        url, params=params, headers=headers, cookies=STATISTA_COOKIES, timeout=30
    )

    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    res = fetch_statista_search("cancer")
    print(res)
