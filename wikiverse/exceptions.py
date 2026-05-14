class WikiLinkSearchError(Exception):
    """Base exception for wikilink-search."""


class PageNotFoundError(WikiLinkSearchError):
    """Raised when a Wikipedia page cannot be found."""


class RequestFailedError(WikiLinkSearchError):
    """Raised when an HTTP request fails."""
