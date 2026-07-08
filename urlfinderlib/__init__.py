def is_url(url: str) -> bool:
    return URL(url).is_url


from urlfinderlib.url import URL
from urlfinderlib.urlfinderlib import find_urls, find_urls_in_text, get_url_permutations
