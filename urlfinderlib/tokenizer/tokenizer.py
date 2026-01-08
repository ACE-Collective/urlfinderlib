import re
from typing import Iterator, List, Union


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
        return (x.group(1) for x in re.finditer(r"(.*?)[.!?]\s", self.utf8_string))

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
        open_indices = self._get_indices_of_sequence(open_sequence)
        closed_indices = self._get_indices_of_sequence(close_sequence)

        index_pairs = []
        for open_index, open_value in enumerate(open_indices):
            for closed_value in closed_indices[:]:
                if open_value < closed_value:
                    index_pairs.append((open_value, closed_value))

                    try:
                        if closed_value < open_indices[open_index + 1]:
                            closed_indices.remove(closed_value)
                    except IndexError:
                        pass

                    if strict:
                        break

        return (self.utf8_string[o + 1 : c] for o, c in index_pairs)

    def get_tokens_between_parentheses(self, strict: bool = True) -> Iterator[str]:
        return self.get_tokens_between_open_and_close_sequence("(", ")", strict=strict)

    def get_tokens_between_sequence(self, sequence: str) -> Iterator[str]:
        indices = self._get_indices_of_sequence(sequence)
        return (x for x in (self.utf8_string[indices[i] + 1 : indices[i + 1]] for i in range(len(indices) - 1)) if x)

    def get_tokens_between_single_quotes(self) -> Iterator[str]:
        return self.get_tokens_between_sequence("'")

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
