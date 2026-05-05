from typing import Set, Union

from icalendar import Calendar

from urlfinderlib.url import URLList

from .html import HtmlUrlFinder
from .text import TextUrlFinder


def _remove_lines_after_end(ical_text: str) -> str:
    lines = ical_text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].upper().startswith("END:"):
            del lines[i]
        else:
            break

    return "\n".join(lines)


class IcalUrlFinder:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, bytes):
            blob = blob.decode("utf-8", errors="ignore")

        text = _remove_lines_after_end(blob)
        blob = text.encode("utf-8", errors="ignore")

        self.blob = blob

    def find_urls(self) -> Set[str]:
        urls = URLList()

        ical = Calendar.from_ical(self.blob)
        for component in ical.walk():
            for _, value in component.property_items():
                # vText/vCalAddress/vUri all subclass str; vDDDTypes/vGeo/etc. don't.
                # BEGIN/END markers come through as bytes.
                if not isinstance(value, str):
                    continue

                fmttype = ""
                params = getattr(value, "params", None)
                if params:
                    fmttype = str(params.get("FMTTYPE", "")).lower()

                if fmttype.startswith("text/html"):
                    urls += HtmlUrlFinder(value).find_urls()
                else:
                    urls += TextUrlFinder(value).find_urls(strict=True)

        return set(urls)
