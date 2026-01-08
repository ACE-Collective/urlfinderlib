from itertools import chain
from typing import Set, Union

import validators

import urlfinderlib.helpers as helpers
import urlfinderlib.tokenizer as tokenizer
from urlfinderlib.url import URLList


class TextUrlFinder:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="ignore")

        self.blob = blob

    def find_urls(self, strict: bool = True, domain_as_url: bool = False) -> Set[str]:
        tok = tokenizer.UTF8Tokenizer(self.blob)

        token_iter = chain(
            tok.get_line_tokens(),
            tok.get_tokens_between_angle_brackets(strict=strict),
            tok.get_tokens_between_backticks(),
            tok.get_tokens_between_brackets(strict=strict),
            tok.get_tokens_between_curly_brackets(strict=strict),
            tok.get_tokens_between_double_quotes(),
            tok.get_tokens_between_parentheses(strict=strict),
            tok.get_tokens_between_single_quotes(),
            tok.get_sentences(),
        )

        split_token_iter = tok.get_split_tokens_after_replace(["<", ">", "`", "[", "]", "{", "}", '"', "'", "(", ")"])

        if domain_as_url:
            tokens = set()
            for token in token_iter:
                if "." in token and "/" in token:
                    tokens.add(token)
                    continue

                if validators.domain(token):
                    tokens.add(token)

            for token in split_token_iter:
                if "." in token and "/" in token:
                    tokens.add(token)
                    continue

                if validators.domain(token):
                    tokens.add(token)
        else:
            tokens = {t for t in token_iter if "." in t and "/" in t}
            tokens |= {t for t in split_token_iter if "." in t and "/" in t}

        valid_urls = URLList()
        for token in tokens:
            # It is common for text files like email plaintext bodies to encode URLs in the form of:
            # http://domain.com<http://actualdomain.com>
            # where the text at the beginning is what will be displayed, and the text inside the <> is the
            # actual URL you will be taken to if you click on it. In these cases, we don't want that entire string
            # to be considered as a valid URL, but would rather have each of them as separate URLs.
            if "<" in token and token.endswith(">"):
                continue

            valid_urls.append(helpers.fix_possible_url(token, domain_as_url=domain_as_url))

        return set(valid_urls)
