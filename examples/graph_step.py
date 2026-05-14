from wikilink_search import WikiClient


wiki = WikiClient(language="en")

state = wiki.page("Artificial intelligence", link_limit=20)
actions = state.links

print("Current state:", state.title)
print("Available actions:")
for index, action in enumerate(actions):
    print(index, action.title)

# Example: choose first link as next action
next_state = wiki.page(actions[0].url, link_limit=20)
print("Next state:", next_state.title)
