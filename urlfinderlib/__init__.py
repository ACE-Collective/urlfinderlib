def is_url(url: str) -> bool:
    return URL(url).is_url


from urlfinderlib.url import URL
from urlfinderlib.urlfinderlib import find_urls, get_url_permutations
