# wikilink-search

A small Python library for searching Wikipedia pages and extracting page titles, summaries, and outgoing hyperlinks.

This project is designed to be useful for search algorithms, graph exploration, tabular reinforcement learning, and DQN environments where Wikipedia pages can be treated as states and hyperlinks as actions.

## Installation

```bash
pip install -e .
```

## Dependencies

```bash
pip install requests beautifulsoup4
```

## Basic usage

```python
from wikiverse import WikiClient

wiki = WikiClient(language="en")

results = wiki.search("Alan Turing", limit=5)
for result in results:
    print(result.title, result.url)

page = wiki.page("Alan Turing")
print(page.title)
print(page.summary)
print(page.links[:10])
```

## Top pages

```python
from wikiverse import WikiClient

wiki = WikiClient(language="en")

top_pages = wiki.top_pages(limit=10)
for page in top_pages:
    print(page.title, page.url)
```

## Why this library?

The main goal is to provide a simple and predictable interface for using Wikipedia as a graph-like environment:

- page = state
- hyperlink = action
- target page = next state

This makes it suitable for experiments with:

- BFS / DFS / A*
- shortest path search
- tabular Q-learning
- SARSA
- DQN
- page navigation agents

## Notes

This MVP uses `requests` and `beautifulsoup4` only. Be respectful with request frequency when scraping Wikipedia.
Use cache and delays in larger experiments.

## License

MIT
