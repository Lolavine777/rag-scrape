from .exceptions import ForumBlockedException

def _do_fetch(url: str) -> str:
    return ""

def fetch_forum_page(url: str) -> str:
    html = _do_fetch(url)
    if "Cloudflare" in html or "Access Denied" in html:
        raise ForumBlockedException("Blocked by Anti-bot")
    return html

def parse_forum_html(html: str) -> str:
    # Dummy implementation for TDD
    return ""
