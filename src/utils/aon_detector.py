"""Utility helpers for Archives of Nethys URL detection."""

from urllib.parse import urlparse

__all__ = ["is_aon_url"]


def is_aon_url(url: str) -> bool:
    """
    Returns True if the URL points to Archives of Nethys (any subdomain),
    ignoring case, query parameters and fragments.
    """
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain.endswith("aonprd.com")
    except Exception:
        return False
