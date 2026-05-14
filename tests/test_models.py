from wikiverse.models import WikiLink, WikiPage, WikiSearchResult


def test_models_can_be_created():
    result = WikiSearchResult(title="Python", url="https://en.wikipedia.org/wiki/Python")
    link = WikiLink(title="Programming language", url="https://en.wikipedia.org/wiki/Programming_language")
    page = WikiPage(title="Python", url=result.url, summary="Summary", links=[link])

    assert result.title == "Python"
    assert page.links[0].title == "Programming language"
