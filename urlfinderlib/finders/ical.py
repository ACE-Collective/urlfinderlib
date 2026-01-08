from typing import Set, Union

from icalendar import Calendar

from urlfinderlib.url import URLList

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
            if component.name == "VEVENT":
                description = component.get("description")
                location = component.get("location")

                if description:
                    urls += TextUrlFinder(description).find_urls(strict=True)

                if location:
                    urls += TextUrlFinder(location).find_urls(strict=True)

        return set(urls)
