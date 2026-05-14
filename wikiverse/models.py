from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class WikiSearchResult:
    """A lightweight result returned by a Wikipedia search."""

    title: str
    url: str
    snippet: Optional[str] = None


@dataclass(frozen=True)
class WikiLink:
    """A hyperlink found inside a Wikipedia page."""

    title: str
    url: str


@dataclass(frozen=True)
class WikiPage:
    """A parsed Wikipedia page."""

    title: str
    url: str
    summary: str
    links: list[WikiLink] = field(default_factory=list)
