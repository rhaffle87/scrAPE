from __future__ import annotations

from bs4 import BeautifulSoup

def parse_html(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, "lxml")
