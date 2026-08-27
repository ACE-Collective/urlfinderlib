from typing import Set, Union

from icalendar.parser import Contentlines, unescape_char

from urlfinderlib.url import URLList

from .html import HtmlUrlFinder
from .text import TextUrlFinder


class IcalUrlFinder:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, bytes):
            blob = blob.decode("utf-8", errors="ignore")

        self.blob = blob

    def find_urls(self) -> Set[str]:
        urls = URLList()

        # Content lines are parsed one at a time instead of through Calendar.from_ical() because that is
        # all-or-nothing: a single line the strict parser rejects (junk "X-FOO; BAR: ..." padding, content
        # after END:VCALENDAR) would otherwise discard every URL in the calendar.
        for line in Contentlines.from_ical(self.blob):
            if not line:
                continue

            try:
                _, params, value = line.parts()
            except ValueError:
                urls += TextUrlFinder(line).find_urls(strict=True)
                continue

            value = unescape_char(value)

            if str(params.get("FMTTYPE", "")).lower().startswith("text/html"):
                urls += HtmlUrlFinder(value).find_urls()
            else:
                urls += TextUrlFinder(value).find_urls(strict=True)

        return set(urls)
