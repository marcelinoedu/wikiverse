from __future__ import annotations

from urllib.parse import quote, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .exceptions import PageNotFoundError, RequestFailedError
from .models import WikiLink, WikiPage, WikiSearchResult


class WikiClient:
    """Simple Wikipedia client based on requests and BeautifulSoup.

    This class intentionally avoids the official Wikipedia API for now so the
    project can stay minimal and easy to understand.
    """

    def __init__(
        self,
        language: str = "en",
        timeout: float = 10.0,
        user_agent: str = "wikilink-search/0.1.0",
    ) -> None:
        self.language = language.strip().lower()
        self.timeout = timeout
        self.base_url = f"https://{self.language}.wikipedia.org"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def search(self, keyword: str, limit: int = 10) -> list[WikiSearchResult]:
        """Search Wikipedia by keyword and return matching pages.

        Parameters
        ----------
        keyword:
            Search text.
        limit:
            Maximum number of results.
        """
        if not keyword.strip():
            return []

        url = f"{self.base_url}/w/index.php"
        params = {"search": keyword, "title": "Special:Search", "fulltext": "1"}
        soup = self._get_soup(url, params=params)

        results: list[WikiSearchResult] = []
        for item in soup.select("li.mw-search-result"):
            anchor = item.select_one("div.mw-search-result-heading a")
            if anchor is None:
                continue

            title = anchor.get_text(strip=True)
            href = anchor.get("href", "")
            page_url = urljoin(self.base_url, href)

            snippet_node = item.select_one("div.searchresult")
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else None

            results.append(WikiSearchResult(title=title, url=page_url, snippet=snippet))
            if len(results) >= limit:
                break

        # Wikipedia may redirect directly to a page when there is an exact match.
        if not results:
            page_title = self._extract_title_from_page(soup)
            canonical_url = self._canonical_url_from_soup(soup) or soup.base.get("href") if soup.base else None
            if page_title:
                results.append(
                    WikiSearchResult(
                        title=page_title,
                        url=canonical_url or self.title_to_url(page_title),
                        snippet=self._extract_summary(soup),
                    )
                )

        return results[:limit]

    def page(self, title_or_url: str, link_limit: int | None = None) -> WikiPage:
        """Fetch a Wikipedia page by title or URL.

        Returns the page title, URL, summary, and outgoing article links.
        """
        if self._looks_like_url(title_or_url):
            url = title_or_url
        else:
            url = self.title_to_url(title_or_url)

        soup = self._get_soup(url)
        title = self._extract_title_from_page(soup)
        if not title:
            raise PageNotFoundError(f"Could not find page: {title_or_url}")

        final_url = self._canonical_url_from_soup(soup) or url
        summary = self._extract_summary(soup)
        links = self._extract_links(soup, limit=link_limit)

        return WikiPage(title=title, url=final_url, summary=summary, links=links)

    def top_pages(self, limit: int = 10) -> list[WikiSearchResult]:
        """Return popular pages from Wikipedia's Special:PopularPages page.

        Availability and exact layout can vary across Wikipedia languages.
        """
        url = f"{self.base_url}/wiki/Special:PopularPages"
        soup = self._get_soup(url)

        results: list[WikiSearchResult] = []

        content = soup.select_one("#mw-content-text") or soup
        for anchor in content.select("a[href^='/wiki/']"):
            href = anchor.get("href", "")
            title = anchor.get_text(" ", strip=True)

            if not title or self._should_skip_href(href):
                continue

            page_url = urljoin(self.base_url, href)
            result = WikiSearchResult(title=title, url=page_url)
            if result not in results:
                results.append(result)

            if len(results) >= limit:
                break

        return results

    def title_to_url(self, title: str) -> str:
        normalized = title.strip().replace(" ", "_")
        return f"{self.base_url}/wiki/{quote(normalized)}"

    def url_to_title(self, url: str) -> str:
        path = urlparse(url).path
        raw_title = path.split("/wiki/", 1)[-1]
        return unquote(raw_title).replace("_", " ")

    def _get_soup(self, url: str, params: dict[str, str] | None = None) -> BeautifulSoup:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RequestFailedError(str(exc)) from exc

        return BeautifulSoup(response.text, "html.parser")

    def _extract_title_from_page(self, soup: BeautifulSoup) -> str:
        heading = soup.select_one("#firstHeading")
        if heading:
            return heading.get_text(" ", strip=True)

        title = soup.select_one("title")
        if title:
            return title.get_text(" ", strip=True).replace(" - Wikipedia", "")

        return ""

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        content = soup.select_one("#mw-content-text") or soup

        paragraphs = []
        for paragraph in content.select("p"):
            text = paragraph.get_text(" ", strip=True)
            if not text:
                continue
            if self._is_low_value_paragraph(text):
                continue
            paragraphs.append(text)
            if len(paragraphs) >= 2:
                break

        return "\n\n".join(paragraphs)

    def _extract_links(self, soup: BeautifulSoup, limit: int | None = None) -> list[WikiLink]:
        content = soup.select_one("#mw-content-text") or soup
        links: list[WikiLink] = []
        seen: set[str] = set()

        for anchor in content.select("a[href^='/wiki/']"):
            href = anchor.get("href", "")
            if self._should_skip_href(href):
                continue

            title = anchor.get("title") or anchor.get_text(" ", strip=True)
            if not title:
                title = self.url_to_title(urljoin(self.base_url, href))

            normalized_url = urljoin(self.base_url, href.split("#", 1)[0])
            if normalized_url in seen:
                continue

            seen.add(normalized_url)
            links.append(WikiLink(title=title.strip(), url=normalized_url))

            if limit is not None and len(links) >= link_limit_safe(limit):
                break

        return links

    def _canonical_url_from_soup(self, soup: BeautifulSoup) -> str | None:
        canonical = soup.select_one("link[rel='canonical']")
        href = canonical.get("href") if canonical else None
        return str(href) if href else None

    def _looks_like_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _should_skip_href(self, href: str) -> bool:
        if not href.startswith("/wiki/"):
            return True

        skipped_prefixes = (
            "/wiki/Special:",
            "/wiki/Help:",
            "/wiki/File:",
            "/wiki/Talk:",
            "/wiki/Category:",
            "/wiki/Template:",
            "/wiki/Portal:",
            "/wiki/Wikipedia:",
            "/wiki/MediaWiki:",
            "/wiki/Module:",
        )
        if href.startswith(skipped_prefixes):
            return True

        return ":" in href.split("/wiki/", 1)[-1]

    def _is_low_value_paragraph(self, text: str) -> bool:
        lowered = text.lower()
        prefixes = (
            "coordinates:",
            "for other uses",
            "this article is about",
            "this article needs",
        )
        return lowered.startswith(prefixes)


def link_limit_safe(limit: int) -> int:
    return max(0, int(limit))
