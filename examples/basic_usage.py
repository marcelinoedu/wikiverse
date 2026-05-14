from wikilink_search import WikiClient


wiki = WikiClient(language="en")

print("Search results:")
for result in wiki.search("Alan Turing", limit=5):
    print("-", result.title, result.url)

print("\nPage:")
page = wiki.page("Alan Turing", link_limit=10)
print(page.title)
print(page.summary[:500])

print("\nLinks:")
for link in page.links:
    print("-", link.title, link.url)
