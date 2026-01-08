import csv
import io
from typing import Set, Union

from urlfinderlib.url import URLList

from .text import TextUrlFinder


class CsvUrlFinder:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="ignore")

        self.blob = blob

    def find_urls(self) -> Set[str]:
        buffer = io.StringIO(self.blob.decode("utf-8", errors="ignore"))
        csv_reader = csv.reader(buffer)
        possible_urls = set()
        for row in csv_reader:
            for item in row:
                if "." in item and "/" in item:
                    possible_urls.add(item)

        urls = URLList()
        for possible_url in possible_urls:
            urls += TextUrlFinder(possible_url).find_urls(strict=True)

        return set(urls)
