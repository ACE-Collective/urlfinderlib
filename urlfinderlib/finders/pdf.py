import re
from itertools import chain
from typing import Set, Union

import urlfinderlib.tokenizer as tokenizer
from urlfinderlib.url import URLList

from .text import TextUrlFinder


class PdfUrlFinder:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="ignore")

        # Replace any stringified hex characters
        self.blob = re.sub(rb"\\x[a-f0-9]{2,}", b" ", blob)

    def find_urls(self) -> Set[str]:
        tok = tokenizer.UTF8Tokenizer(self.blob)

        # TODO: itertools.product(*zip(string.lower(), string.upper()))
        token_iter = chain(
            tok.get_tokens_between_open_and_close_sequence("/URI", ">>", strict=True),
            tok.get_tokens_between_open_and_close_sequence("(http", ")", strict=True),
            tok.get_tokens_between_open_and_close_sequence("(ftp", ")", strict=True),
            tok.get_tokens_between_open_and_close_sequence("<http", ">", strict=True),
            tok.get_tokens_between_open_and_close_sequence("<ftp", ">", strict=True),
            tok.get_tokens_between_open_and_close_sequence('"http', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence('"ftp', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence("'http", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence("'ftp", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence("(HTTP", ")", strict=True),
            tok.get_tokens_between_open_and_close_sequence("(FTP", ")", strict=True),
            tok.get_tokens_between_open_and_close_sequence("<HTTP", ">", strict=True),
            tok.get_tokens_between_open_and_close_sequence("<FTP", ">", strict=True),
            tok.get_tokens_between_open_and_close_sequence('"HTTP', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence('"FTP', '"', strict=True),
            tok.get_tokens_between_open_and_close_sequence("'HTTP", "'", strict=True),
            tok.get_tokens_between_open_and_close_sequence("'FTP", "'", strict=True),
        )

        urls = URLList()
        for token in token_iter:
            token = token.replace("\\", "")

            # Since various characters in the PDF were replaced with spaces, we assume that there should not
            # be any spaces in URLs that get extracted.
            token = token.split()[0]

            urls += TextUrlFinder(token).find_urls()

        return set(urls)
