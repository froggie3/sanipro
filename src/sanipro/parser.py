import logging
import re
import typing
from dataclasses import dataclass
from enum import Enum, auto

from sanipro.abc import ParserInterface, TokenInterface
from sanipro.delimiter import Delimiter


class UseDelimiterMixin:
    """Injects delimiter to split the prompt."""

    def __init__(self, delimiter: Delimiter) -> None:
        self._delimiter = delimiter


class InvalidSyntaxError(Exception):
    pass


class ParserState(Enum):
    DEFAULT = auto()
    ESCAPED = auto()
    IN_PARENTHESIS = auto()
    ESCAPED_IN_PARENTHESIS = auto()
    AFTER_COLON = auto()
    EMPHASIS_END = auto()
    FAILED_PARENTHESIS = auto()
    AFTER_FAILED = auto()
    PARTIAL_EMPHASIS = auto()
    ESCAPED_PARTIAL = auto()
    AFTER_DELIMITER = auto()


def parse_bad_tuple(token: str, token_cls: type[TokenInterface]) -> TokenInterface:
    """
    Split an emphasized token into left and right sides with `:`.
    The right side separated by the last colon is adopted as the strength
    even when there are three or more elements.
    """

    pattern = r"\((.*):(\d+(?:\.\d+)?)\)"
    m = re.match(pattern, token)
    if m:
        prompt_name = m.group(1)
        prompt_weight = m.group(2)
        try:
            return token_cls(prompt_name, float(prompt_weight or "1.0"))
        except ValueError:
            raise

    raise InvalidSyntaxError("pattern not found")


class ParenState(Enum):
    DEFAULT = auto()
    ESCAPED = auto()


@dataclass
class ParenContext:
    """Context class for searching parentheses."""

    prompt: str
    start: int
    n_parens_start: int
    n_parens_last: int
    current_index: int
    state: ParenState


class PairedParenthesesFinder:
    def __init__(self, prompt: str, start: int, n_parens_start: int) -> None:
        self.ctx = ParenContext(
            prompt=prompt,
            start=start,
            n_parens_start=n_parens_start,
            n_parens_last=n_parens_start,
            current_index=start,
            state=ParenState.DEFAULT,
        )

    def handle_default(self, char: str) -> ParenState | None:
        if char == "\\":
            return ParenState.ESCAPED
        elif char == "(":
            self.ctx.n_parens_last += 1
        elif char == ")":
            self.ctx.n_parens_last -= 1
            if self.ctx.n_parens_start == self.ctx.n_parens_last:
                return None  # found
        return ParenState.DEFAULT

    def handle_escaped(self, char: str) -> ParenState:
        if char in "()":
            return ParenState.DEFAULT
        return ParenState.ESCAPED

    def find_last_paren(self) -> int | None:
        """
        Skip through the buffer until n_parens_last is at the same level
        as the original n_parens, and returns the position of the last ')'.
        """

        handlers = {
            ParenState.DEFAULT: self.handle_default,
            ParenState.ESCAPED: self.handle_escaped,
        }

        while self.ctx.current_index < len(self.ctx.prompt):
            char = self.ctx.prompt[self.ctx.current_index]

            handler = handlers[self.ctx.state]
            next_state = handler(char)

            # found
            if next_state is None:
                return self.ctx.current_index

            self.ctx.state = next_state
            self.ctx.current_index += 1

        return None


class _CharStack(list):
    def __str__(self) -> str:
        return "".join(self)

    def join(self) -> str:
        return self.__str__()


class _PromptName(_CharStack):
    pass


class _PromptWeight(_CharStack):
    pass


@dataclass
class ParserContext:
    """Context class that holds the parser state."""

    prompt: str
    token_cls: type[TokenInterface]
    delimiter: str
    tokens: list[TokenInterface]
    prompt_name: _PromptName
    prompt_weight: _PromptWeight
    idx_last_delimiter: int
    n_parens: int
    current_index: int
    state: ParserState

    def __repr__(self) -> str:
        args = [
            f"{self.current_index:<5d}",
            f"{self.prompt[self.current_index]:5s}",
            f"{self.state:30s}",
            f"{self.idx_last_delimiter:<5d}",
            f"{self.prompt_name.join():5s}",
            f"{self.prompt_weight.join():5s}",
        ]
        return "  ".join(args)

    def _debug(self) -> None:
        print(self.__repr__())


class NormalParser(ParserInterface, UseDelimiterMixin):
    """Uses a delimiter to split the prompt."""


class DummyParser(NormalParser):
    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
    ) -> typing.Generator[TokenInterface, None, None]:
        return (
            token_cls(element.strip(), 1.0)
            for element in sentence.strip().split(self._delimiter.sep_input)
        )


class A1111Parser(NormalParser):
    ctx: ParserContext

    def is_special_char(self, char: str) -> bool:
        return char in f"\\(){self.ctx.delimiter}"

    def try_add_if_special_char_or_error(
        self, char: str, return_state: ParserState
    ) -> ParserState:
        if not self.is_special_char(char):
            raise InvalidSyntaxError("no special token was found after '\\'")
        self.ctx.prompt_name.append(char)
        return return_state

    def _handle_default(self, char: str) -> ParserState:
        if char == "\\":
            return ParserState.ESCAPED
        elif char == "(":
            self.ctx.n_parens += 1
            return ParserState.IN_PARENTHESIS
        elif char == ")":
            raise InvalidSyntaxError("could not find the start '('")
        elif char == self.ctx.delimiter:
            prompt_name_concat = self.ctx.prompt_name.join()
            self.ctx.prompt_name.clear()
            self.ctx.tokens.append(self.ctx.token_cls(prompt_name_concat, 1.0))
            self.ctx.idx_last_delimiter = self.ctx.current_index
            return ParserState.AFTER_DELIMITER
        else:
            self.ctx.prompt_name.append(char)
            return ParserState.DEFAULT

    def _handle_after_delimiter(self, char: str) -> ParserState:
        if char == " ":
            self.ctx.idx_last_delimiter = self.ctx.current_index
            return ParserState.AFTER_DELIMITER
        elif char == "\\":
            return ParserState.ESCAPED
        elif char == "(":
            self.ctx.n_parens += 1
            return ParserState.IN_PARENTHESIS
        elif char == ")":
            raise InvalidSyntaxError
        elif char == self.ctx.delimiter:
            prompt_name_concat = self.ctx.prompt_name.join()
            self.ctx.prompt_name.clear()
            self.ctx.tokens.append(self.ctx.token_cls(prompt_name_concat, 1.0))
            return ParserState.AFTER_DELIMITER
        else:
            self.ctx.prompt_name.append(char)
            return ParserState.DEFAULT

    def _handle_escaped(self, char: str) -> ParserState:
        return self.try_add_if_special_char_or_error(char, ParserState.DEFAULT)

    def _handle_in_parenthesis(self, char: str) -> ParserState:
        if char == "\\":
            return ParserState.ESCAPED_IN_PARENTHESIS
        elif char == ":":
            return ParserState.AFTER_COLON
        elif char == "(":
            index_last_paren = PairedParenthesesFinder(
                self.ctx.prompt, self.ctx.current_index, self.ctx.n_parens
            ).find_last_paren()
            if index_last_paren is None:
                raise InvalidSyntaxError("unclosed parensis detected")

            tmp_buffer = self.ctx.prompt[self.ctx.current_index : index_last_paren + 1]
            self.ctx.prompt_name.extend(tmp_buffer)
            self.ctx.current_index = index_last_paren
            return ParserState.IN_PARENTHESIS
        elif char == ")":
            raise InvalidSyntaxError(
                "the emphasis syntax in a1111 requires a value after a colon"
            )
        else:
            self.ctx.prompt_name.append(char)
            return ParserState.IN_PARENTHESIS

    def _handle_escaped_in_parenthesis(self, char: str) -> ParserState:
        return self.try_add_if_special_char_or_error(char, ParserState.IN_PARENTHESIS)

    def _handle_after_colon(self, char: str) -> ParserState:
        if char == ")":
            self.ctx.n_parens -= 1
            return ParserState.EMPHASIS_END
        else:
            self.ctx.prompt_weight.append(char)
            return ParserState.AFTER_COLON

    def _handle_emphasis_end(self, char: str) -> ParserState:
        if char == self.ctx.delimiter:
            prompt_name_concat = self.ctx.prompt_name.join()
            prompt_weight_concat = self.ctx.prompt_weight.join()

            self.ctx.prompt_name.clear()
            self.ctx.prompt_weight.clear()

            try:
                self.ctx.tokens.append(
                    self.ctx.token_cls(prompt_name_concat, float(prompt_weight_concat))
                )
                return ParserState.AFTER_DELIMITER
            except ValueError:
                self.ctx.current_index = self.ctx.idx_last_delimiter
                return ParserState.FAILED_PARENTHESIS
        else:
            self.ctx.prompt_name.clear()
            self.ctx.prompt_weight.clear()
            self.ctx.current_index = self.ctx.idx_last_delimiter
            return ParserState.PARTIAL_EMPHASIS

    def _handle_failed_parenthesis(self, char: str) -> ParserState:
        if char == "(":
            index_last_paren = PairedParenthesesFinder(
                self.ctx.prompt, self.ctx.current_index, self.ctx.n_parens
            ).find_last_paren()
            if index_last_paren is None:
                raise InvalidSyntaxError("unclosed parensis detected")

            tmp_buffer = self.ctx.prompt[self.ctx.current_index : index_last_paren + 1]
            self.ctx.prompt_name.extend(tmp_buffer)
            self.ctx.current_index = index_last_paren
            return ParserState.AFTER_FAILED
        else:
            # consume until next '('
            return ParserState.FAILED_PARENTHESIS

    def _handle_after_failed(self, char: str) -> ParserState:
        if char == self.ctx.delimiter:
            p_concat = self.ctx.prompt_name.join()
            self.ctx.prompt_name.clear()
            self.ctx.prompt_weight.clear()

            try:
                self.ctx.tokens.append(parse_bad_tuple(p_concat, self.ctx.token_cls))
                return ParserState.AFTER_DELIMITER
            except ValueError:
                logging.exception(
                    f"parsing was failed at {char!r} in {p_concat!r}, try backslash escaping"
                )
                raise
        else:
            return ParserState.AFTER_FAILED

    def _handle_partial_emphasis(self, char: str) -> ParserState:
        if char == "\\":
            return ParserState.ESCAPED_PARTIAL
        elif char == self.ctx.delimiter:
            prompt_name_concat = self.ctx.prompt_name.join()
            self.ctx.prompt_name.clear()
            self.ctx.tokens.append(self.ctx.token_cls(prompt_name_concat, 1.0))
            return ParserState.AFTER_DELIMITER
        else:
            self.ctx.prompt_name.append(char)
            return ParserState.PARTIAL_EMPHASIS

    def _handle_escaped_partial(self, char: str) -> ParserState:
        return self.try_add_if_special_char_or_error(char, ParserState.PARTIAL_EMPHASIS)

    def parse_prompt(
        self, prompt: str, token_cls: type[TokenInterface], delimiter: str
    ) -> list[TokenInterface]:
        self.ctx = ParserContext(
            prompt=prompt,
            token_cls=token_cls,
            delimiter=delimiter,
            tokens=[],
            prompt_name=_PromptName(),
            prompt_weight=_PromptWeight(),
            # assuming invisible delimiter would be at the start of the prompt
            idx_last_delimiter=-1,
            n_parens=0,
            current_index=0,
            state=ParserState.DEFAULT,
        )

        handlers = {
            ParserState.DEFAULT: self._handle_default,
            ParserState.ESCAPED: self._handle_escaped,
            ParserState.IN_PARENTHESIS: self._handle_in_parenthesis,
            ParserState.ESCAPED_IN_PARENTHESIS: self._handle_escaped_in_parenthesis,
            ParserState.AFTER_COLON: self._handle_after_colon,
            ParserState.EMPHASIS_END: self._handle_emphasis_end,
            ParserState.FAILED_PARENTHESIS: self._handle_failed_parenthesis,
            ParserState.AFTER_FAILED: self._handle_after_failed,
            ParserState.PARTIAL_EMPHASIS: self._handle_partial_emphasis,
            ParserState.ESCAPED_PARTIAL: self._handle_escaped_partial,
            ParserState.AFTER_DELIMITER: self._handle_after_delimiter,
        }

        while self.ctx.current_index < len(prompt):
            char = prompt[self.ctx.current_index]
            handler = handlers[self.ctx.state]
            self.ctx.state = handler(char)
            self.ctx.current_index += 1

        tokens = self.ctx.tokens

        del self.ctx
        return tokens

    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
    ) -> typing.Generator[TokenInterface, None, None]:
        for token in self.parse_prompt(sentence, token_cls, self._delimiter.sep_input):
            yield token


if __name__ == "__main__":
    import doctest

    doctest.testmod()
