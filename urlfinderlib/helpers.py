import base64
from urllib.parse import urlsplit

import validators


def build_url(scheme: str, netloc: str, path: str) -> str:
    return f"{scheme}://{netloc}{path}"


def fix_possible_url(value: str, domain_as_url: bool = False) -> str:
    value = fix_possible_value(value)
    return value if validators.email(value) else prepend_missing_scheme(value, domain_as_url=domain_as_url)


def fix_possible_value(value: str) -> str:
    value = value.strip()
    value = remove_hidden_unicode_characters(value)
    value = fix_slashes(value)
    value = fix_scheme(value)
    value = remove_mailto_if_not_email_address(value)
    value = remove_null_characters(value)
    value = remove_surrounding_quotes(value)
    return value


def fix_scheme(value: str) -> str:
    try:
        split_value = urlsplit(value)
    except ValueError:
        return ""

    if split_value.scheme and not split_value.netloc and split_value.path:
        return f"{split_value.scheme}://{split_value.path.lstrip('/')}"

    return value


def fix_slashes(value: str) -> str:
    value = value.replace("\\", "/")

    if "://" not in value:
        return value.replace(":/", "://")

    return value


def get_ascii_url(url: str) -> str:
    return url.encode("ascii", errors="ignore").decode()


def is_base64_ascii(value: str) -> bool:
    try:
        base64.b64decode(f"{value}===").decode("ascii")
        return True
    except:
        return False


def might_be_html(value: bytes) -> bool:
    html_characters = [b"<", b">", b"=", b":", b"/"]
    return all(html_character in value for html_character in html_characters)


def prepend_missing_scheme(value: str, domain_as_url: bool = False) -> str:
    value = value.lstrip(":/")

    try:
        split_value = urlsplit(value)
    except ValueError:
        return value

    if domain_as_url:
        if not split_value.scheme and "." in value:
            value = f"https://{value}"
    else:
        if not split_value.scheme and "/" in value:
            value = f"https://{value}"

    return value


def remove_hidden_unicode_characters(value: str) -> str:
    # http://www.unicode.org/faq/unsup_char.html
    hidden_characters = ["\u200c", "\u200d", "\u200e", "\u00ad", "\u2060", "\ufeff", "\u200b", "\u2061", "\u115f"]

    for hidden_character in hidden_characters:
        value = value.replace(hidden_character, "")

    return value


def remove_surrounding_quotes(value: str) -> str:
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    return value


def remove_mailto_if_not_email_address(value: str) -> str:
    try:
        split_value = urlsplit(value)
    except ValueError:
        return value

    if split_value.scheme == "mailto" and not validators.email(split_value.path):
        return value[7:]

    return value


def remove_null_characters(value: str) -> str:
    return value.replace("\u0000", "")
