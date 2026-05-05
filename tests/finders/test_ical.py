import urlfinderlib.finders as finders


def test_create_text():
    assert finders.IcalUrlFinder("test")


def _calendar(properties: str) -> str:
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Test//Test//EN\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:uid@example.com\r\n"
        "DTSTAMP:20260101T000000Z\r\n"
        "DTSTART:20260515T090000Z\r\n"
        "DTEND:20260515T100000Z\r\n"
        f"{properties}"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


def test_x_alt_desc_html():
    """Regression: URL inside X-ALT-DESC with FMTTYPE=text/html should be extracted."""
    ical = _calendar(
        "X-ALT-DESC;FMTTYPE=text/html:.<a href='https://example.com/d/abcd-efg-123'>"
        "CLICK HERE TO DOWNLOAD DOCUMENT</a>.\r\n"
    )
    assert finders.IcalUrlFinder(ical).find_urls() == {"https://example.com/d/abcd-efg-123"}


def test_description_plain_text():
    ical = _calendar("DESCRIPTION:see https://example.com/desc for details\r\n")
    assert finders.IcalUrlFinder(ical).find_urls() == {"https://example.com/desc"}


def test_location_plain_text():
    ical = _calendar("LOCATION:meeting at https://example.com/loc\r\n")
    assert finders.IcalUrlFinder(ical).find_urls() == {"https://example.com/loc"}


def test_summary_plain_text():
    ical = _calendar("SUMMARY:agenda at https://example.com/summary\r\n")
    assert finders.IcalUrlFinder(ical).find_urls() == {"https://example.com/summary"}


def test_vtodo_component():
    """URLs in non-VEVENT components should also be extracted."""
    ical = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Test//Test//EN\r\n"
        "BEGIN:VTODO\r\n"
        "UID:todo@example.com\r\n"
        "DTSTAMP:20260101T000000Z\r\n"
        "DESCRIPTION:complete task at https://example.com/todo\r\n"
        "END:VTODO\r\n"
        "END:VCALENDAR\r\n"
    )
    assert finders.IcalUrlFinder(ical).find_urls() == {"https://example.com/todo"}


def test_no_urls():
    ical = _calendar("SUMMARY:lunch\r\nLOCATION:cafeteria\r\n")
    assert finders.IcalUrlFinder(ical).find_urls() == set()


def test_non_text_properties_do_not_crash():
    """Date/recurrence properties should be skipped, not raise."""
    ical = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Test//Test//EN\r\n"
        "BEGIN:VEVENT\r\n"
        "UID:rec@example.com\r\n"
        "DTSTAMP:20260101T000000Z\r\n"
        "DTSTART:20260515T090000Z\r\n"
        "DTEND:20260515T100000Z\r\n"
        "RRULE:FREQ=WEEKLY;COUNT=4\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    assert finders.IcalUrlFinder(ical).find_urls() == set()
