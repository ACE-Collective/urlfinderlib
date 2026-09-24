import re
from bisect import bisect_right
from itertools import chain
from typing import Iterator, List, Union

_SENTENCE_TERMINATOR = re.compile(r"[.!?]\s")


class UTF8Tokenizer:
    def __init__(self, blob: Union[bytes, str]):
        if isinstance(blob, str):
            blob = blob.encode("utf-8", errors="ignore")

        self.blob = blob
        self.utf8_string = self.blob.decode("utf-8", errors="ignore")

    def get_line_tokens(self) -> Iterator[str]:
        return (x.group(0) for x in re.finditer(r"[^\n\r]+", self.utf8_string))

    def get_split_tokens(self) -> Iterator[str]:
        return (x.group(0) for x in re.finditer(r"[^\s]+", self.utf8_string))

    def get_split_tokens_after_replace(self, replace_tokens: List[str]) -> Iterator[str]:
        new_tokenizer = self._get_new_tokenizer_with_replaced_characters(replace_tokens)
        return new_tokenizer.get_split_tokens()

    def get_ascii_strings(self, length: int = 4) -> Iterator[str]:
        pattern = b"[\x20-\x7e]{%b,}" % str(length).encode("ascii", errors="ignore")
        return (x.group(0).decode("ascii") for x in re.finditer(pattern, self.blob))

    def get_sentences(self) -> Iterator[str]:
        # Same output as re.finditer(r"(.*?)[.!?]\s", s), whose lazy prefix retries from every position of a
        # line with no terminator and so is quadratic in the line length (minified JavaScript). A sentence runs
        # from the end of the previous terminator, or from just after the last newline before this terminator
        # if one comes later, since "." matches anything but a newline.
        s = self.utf8_string
        pos = 0
        for match in _SENTENCE_TERMINATOR.finditer(s):
            end = match.start()
            newline = s.rfind("\n", pos, end)
            yield s[newline + 1 if newline >= pos else pos : end]
            pos = match.end()

    def get_tokens_between_angle_brackets(self, strict: bool = True) -> Iterator[str]:
        return self.get_tokens_between_open_and_close_sequence("<", ">", strict=strict)

    def get_tokens_between_backticks(self) -> Iterator[str]:
        return self.get_tokens_between_sequence("`")

    def get_tokens_between_brackets(self, strict: bool = True) -> Iterator[str]:
        return self.get_tokens_between_open_and_close_sequence("[", "]", strict=strict)

    def get_tokens_between_curly_brackets(self, strict: bool = True) -> Iterator[str]:
        return self.get_tokens_between_open_and_close_sequence("{", "}", strict=strict)

    def get_tokens_between_double_quotes(self) -> Iterator[str]:
        return self.get_tokens_between_sequence('"')

    def get_tokens_between_open_and_close_sequence(
        self, open_sequence: str, close_sequence: str, strict: bool = True
    ) -> Iterator[str]:
        # Each opening sequence pairs with the first closing sequence after it (strict), or with every
        # closing sequence after it. Both index lists are sorted, so a binary search finds the first
        # one; scanning the list from the start for every opening sequence is quadratic.
        open_indices = self._get_indices_of_sequence(open_sequence)
        closed_indices = self._get_indices_of_sequence(close_sequence)

        index_pairs = []
        for open_value in open_indices:
            first = bisect_right(closed_indices, open_value)
            if strict:
                if first < len(closed_indices):
                    index_pairs.append((open_value, closed_indices[first]))
            else:
                index_pairs.extend((open_value, closed_value) for closed_value in closed_indices[first:])

        return (self.utf8_string[o + 1 : c] for o, c in index_pairs)

    def get_tokens_between_parentheses(self, strict: bool = True) -> Iterator[str]:
        return self.get_tokens_between_open_and_close_sequence("(", ")", strict=strict)

    def get_tokens_between_sequence(self, sequence: str) -> Iterator[str]:
        indices = self._get_indices_of_sequence(sequence)
        return (x for x in (self.utf8_string[indices[i] + 1 : indices[i + 1]] for i in range(len(indices) - 1)) if x)

    def get_tokens_between_single_quotes(self) -> Iterator[str]:
        return chain(
            self.get_tokens_between_sequence("'"),
            self.get_tokens_between_sequence("\u2018"),
            self.get_tokens_between_sequence("\u2019"),
        )

    def get_tokens_between_spaces(self) -> Iterator[str]:
        return self.get_tokens_between_sequence(" ")

    def get_tokens_between_spaces_after_replace(self, replace_tokens: List[str]) -> Iterator[str]:
        new_tokenizer = self._get_new_tokenizer_with_replaced_characters(replace_tokens)
        return new_tokenizer.get_tokens_between_spaces()

    def _get_indices_of_sequence(self, sequence: str) -> List[int]:
        return [m.start() for m in re.finditer(re.escape(sequence), self.utf8_string)]

    def _get_new_tokenizer_with_replaced_characters(self, replace_tokens: List[str]) -> "UTF8Tokenizer":
        new_tokenizer = UTF8Tokenizer(self.utf8_string.encode("utf-8"))
        for b in replace_tokens:
            new_tokenizer.utf8_string = new_tokenizer.utf8_string.replace(b, " ")

        return new_tokenizer
