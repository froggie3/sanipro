import re
from dataclasses import dataclass
from enum import Enum, auto

from sanipro.abc import TokenInterface
from sanipro.parser import InvalidSyntaxError


class CharStack(list):
    """Stack for storing characters"""

    def __str__(self) -> str:
        return "".join(self)

    def join(self) -> str:
        return self.__str__()


class PromptWeight(CharStack):
    """Storing 'weight' characters."""


class PromptName(CharStack):
    """Storing 'name' characters."""


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


class ParserState(Enum):
    DEFAULT = auto()
    LINE_BREAK = auto()
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


TokenGroup = list[list[TokenInterface]]


@dataclass
class A1111ParserContext:
    """Context class that holds the parser state."""

    prompt: str
    tokens: list[TokenInterface]
    token_cls: type[TokenInterface]
    delimiter: str
    prompt_name: PromptName
    prompt_weight: PromptWeight
    idx_last_delimiter: int
    n_parens: int
    current_index: int
    state: ParserState

    def __repr__(self) -> str:
        args = [
            f"{self.current_index:<5d}",
            f"{self.__debug_char():5s}",
            f"{self.state:30s}",
            f"{self.idx_last_delimiter:<5d}",
            f"{self.prompt_name.join():5s}",
            f"{self.prompt_weight.join():5s}",
        ]
        return "  ".join(args)

    @property
    def char(self):
        return self.prompt[self.current_index]

    def __debug_char(self) -> str:
        if self.char.isprintable():
            return self.char
        return "<%s>" % (ord(self.char),)

    def _debug(self) -> None:
        print(self.__repr__())


@dataclass
class A1111ParserUngroupedContext(A1111ParserContext):
    pass


@dataclass
class A1111ParserGroupedContext(A1111ParserContext):
    token_groups: TokenGroup


def parse_bad_tuple(token: str, token_cls: type[TokenInterface]) -> TokenInterface:
    """
    Split an emphasized token into left and right sides with `:`.
    The right side separated by the last colon is adopted as the strength
    even when there are three or more elements.
    """

    pattern = r"\((.*):([+-]?\d+(?:\.\d+)?)\)"
    m = re.match(pattern, token)
    if m:
        prompt_name = m.group(1)
        prompt_weight = m.group(2)
        try:
            return token_cls(prompt_name, float(prompt_weight or "1.0"))
        except ValueError:
            raise

    raise InvalidSyntaxError("pattern not found")


def find_last_paren(prompt: str, start: int, n_parens_start: int) -> int | None:
    """
    Skip through the buffer until n_parens_last is at the same level
    as the original n_parens, and returns the position of the last ')'.
    """
    ctx = ParenContext(
        prompt=prompt,
        start=start,
        n_parens_start=n_parens_start,
        n_parens_last=n_parens_start,
        current_index=start,
        state=ParenState.DEFAULT,
    )

    def handle_default(char: str) -> ParenState | None:
        if char == "\\":
            return ParenState.ESCAPED
        elif char == "(":
            ctx.n_parens_last += 1
        elif char == ")":
            ctx.n_parens_last -= 1
            if ctx.n_parens_start == ctx.n_parens_last:
                return None  # found
        return ParenState.DEFAULT

    def handle_escaped(char: str) -> ParenState:
        if char in "()":
            return ParenState.DEFAULT
        return ParenState.ESCAPED

    handlers = {ParenState.DEFAULT: handle_default, ParenState.ESCAPED: handle_escaped}

    while ctx.current_index < len(prompt):
        char = prompt[ctx.current_index]

        handler = handlers[ctx.state]
        next_state = handler(char)

        # found
        if next_state is None:
            return ctx.current_index

        ctx.state = next_state
        ctx.current_index += 1

    return None
