import re
import typing

from sanipro.abc import ParserInterface, TokenInterface
from sanipro.compatible import Self


class Token(TokenInterface):
    _delimiter: str

    def __init__(self, name: str, weight: float) -> None:
        self._name = name
        self._weight = float(weight)

    @property
    def name(self) -> str:
        return self._name

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def length(self) -> int:
        return len(self.name)

    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> Self:
        if new_name is None:
            new_name = self._name
        if new_weight is None:
            new_weight = self._weight

        return type(self)(new_name, new_weight)

    def __repr__(self) -> str:
        items = (f"{v!r}" for v in (self.name, self.weight))
        return "{}({})".format(type(self).__name__, f", ".join(items))

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError
        return self._name == other._name and self._weight == other._weight

    def __hash__(self) -> int:
        return hash((self._name, self._weight))


class TokenInteractive(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)
        self._delimiter = ":"

    def __str__(self) -> str:
        if self.weight != 1.0:
            return f"({self.name}{self._delimiter}{self.weight})"
        return self.name


class TokenNonInteractive(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)
        # defining 'delimiter' between token and weight helps to
        # pass the result of this command to like `column -t -s"\t"`
        self._delimiter = "\t"

    def __str__(self) -> str:
        return f"{self.name}{self._delimiter}{self.weight}"


class DummyParser(ParserInterface):
    @staticmethod
    def get_token(
        token_cls: type[TokenInterface], sentence: str, delimiter: str | None = None
    ) -> typing.Generator[TokenInterface, None, None]:
        if delimiter is not None:
            for element in sentence.strip().split(delimiter):
                yield token_cls(element.strip(), 1.0)


def find_last_paren(prompt: str, start: int, n_parens_start: int) -> int:
    """Skip through the buffer until n_parens_last is at the same level
    as the original n_parens, and returns the position of the last ')'."""

    index_last_paren = start
    n_parens_last = n_parens_start
    i = start

    while i < len(prompt):
        char_in_paren = prompt[i]

        if char_in_paren == "(":
            n_parens_last += 1
        elif char_in_paren == ")":
            n_parens_last -= 1
            index_last_paren = i
            if n_parens_start == n_parens_last:
                return i
        i += 1

    return i


class ParserV1(ParserInterface):
    @staticmethod
    def parse_prompt(
        prompt: str, token_cls: type[TokenInterface], delimiter: str
    ) -> list[TokenInterface]:
        """
        split `token_combined` into left and right sides with `:`
        when there are three or more elements,
        the right side separated by the last colon is adopted as the weight.

        >>> from lib.common import PromptInteractive, PromptNonInteractive

        >>> parse_line('brown hair:1.2', PromptInteractive)
        PromptInteractive('brown hair', 1.2)

        >>> parse_line('1girl', PromptInteractive)
        PromptInteractive('1girl', 1.0)

        >>> parse_line(':3', PromptInteractive)
        PromptInteractive(':3', 1.2)

        >>> parse_line('(re:zero kara hajimeru isekai seikatsu:1.2)', PromptInteractive)
        PromptInteractive('re:zero kara hajimeru isekai seikatsu', 1.2)

        >>> parse_line('(re:zero kara hajimeru isekai seikatsu)', PromptInteractive)
        PromptInteractive('re:zero kara hajimeru isekai seikatsu', 1.0)
        """

        tokens = []
        prompt_name = []
        prompt_weight = []
        m_general = 00
        n_parens = 0
        i = 0

        while i < len(prompt):
            char = prompt[i]

            if m_general == 00:  # default
                if char == "\\":
                    prompt_name.append(char)
                    m_general = 10
                elif char == "(":
                    m_general = 20
                    n_parens += 1
                elif char == ")":
                    m_general = 00
                elif char == delimiter:  # prompt was ended without emphasis.
                    prompt_name_concat = "".join(prompt_name).strip()
                    prompt_name.clear()
                    tokens.append(token_cls(prompt_name_concat, 1.0))
                    m_general = 00
                else:
                    prompt_name.append(char)
                    m_general = 00

            elif m_general == 10:  # in escaped
                prompt_name.append(char)
                m_general = 00

            elif m_general == 11:  # in parenthesis, and escaped
                prompt_name.append(char)
                m_general = 20

            elif m_general == 20:  # in parenthesis
                if char == "\\":
                    m_general = 11
                elif char == ":":
                    m_general = 30
                elif char == "(":
                    index_last_paren = find_last_paren(prompt, i, n_parens)
                    tmp_buffer = prompt[i : index_last_paren + 1]
                    prompt_name.extend(tmp_buffer)

                    i = index_last_paren
                    m_general = 20
                elif char == ")":
                    raise ValueError(
                        "the emphasis syntax in a1111 requires a value after a colon"
                    )
                else:
                    prompt_name.append(char)
                    m_general = 20

            elif m_general == 30:  # after a colon
                if char == ")":
                    m_general = 50
                    n_parens -= 1
                else:
                    prompt_weight.append(char)
                    m_general = 30

            elif m_general == 50:  # prompt was ended with emphasis.
                if char == delimiter:
                    prompt_name_concat = "".join(prompt_name).strip()
                    prompt_weight_concat = "".join(prompt_weight).strip()
                    prompt_name.clear()
                    prompt_weight.clear()
                    tokens.append(
                        token_cls(prompt_name_concat, float(prompt_weight_concat))
                    )
                    m_general = 00

            i += 1

        return tokens

    @classmethod
    def get_token(
        cls,
        token_cls: type[TokenInterface],
        sentence: str,
        delimiter: str | None = None,
    ) -> typing.Generator[TokenInterface, None, None]:
        if delimiter is not None:
            return (token for token in cls.parse_prompt(sentence, token_cls, delimiter))


class ParserV2(ParserInterface):
    re_attention = re.compile(
        r"""
    \\\(|
    \\\)|
    \\\[|
    \\]|
    \\\\|
    \\|
    \(|
    \[|
    :([+-]?[.\d]+)\)|
    \)|
    ]|
    [^\\()\[\]:]+|
    :
    """,
        re.X,
    )

    re_break = re.compile(r"\s*\bBREAK\b\s*", re.S)

    @classmethod
    def parse_prompt_attention(cls, text: str) -> list[list]:
        """
        Parses a string with attention tokens and returns a list of pairs: text and its associated weight.
        Accepted tokens are:
        (abc) - increases attention to abc by a multiplier of 1.1
        (abc:3.12) - increases attention to abc by a multiplier of 3.12
        [abc] - decreases attention to abc by a multiplier of 1.1
        \( - literal character '('
        \[ - literal character '['
        \) - literal character ')'
        \] - literal character ']'
        \\ - literal character '\'
        anything else - just text

        >>> parse_prompt_attention('normal text')
        [['normal text', 1.0]]
        >>> parse_prompt_attention('an (important) word')
        [['an ', 1.0], ['important', 1.1], [' word', 1.0]]
        >>> parse_prompt_attention('(unbalanced')
        [['unbalanced', 1.1]]
        >>> parse_prompt_attention('\(literal\]')
        [['(literal]', 1.0]]
        >>> parse_prompt_attention('(unnecessary)(parens)')
        [['unnecessaryparens', 1.1]]
        >>> parse_prompt_attention('a (((house:1.3)) [on] a (hill:0.5), sun, (((sky))).')
        [['a ', 1.0],
        ['house', 1.5730000000000004],
        [' ', 1.1],
        ['on', 1.0],
        [' a ', 1.1],
        ['hill', 0.55],
        [', sun, ', 1.1],
        ['sky', 1.4641000000000006],
        ['.', 1.1]]
        """

        res: list = []
        round_brackets = []
        square_brackets = []

        round_bracket_multiplier = 1.1
        square_bracket_multiplier = 1 / 1.1

        def multiply_range(start_position, multiplier):
            for p in range(start_position, len(res)):
                res[p][1] *= multiplier

        for m in cls.re_attention.finditer(text):
            text = m.group(0)
            weight = m.group(1)

            if text.startswith("\\"):
                res.append([text[1:], 1.0])
            elif text == "(":
                round_brackets.append(len(res))
            elif text == "[":
                square_brackets.append(len(res))
            elif weight is not None and len(round_brackets) > 0:
                multiply_range(round_brackets.pop(), float(weight))
            elif text == ")" and len(round_brackets) > 0:
                multiply_range(round_brackets.pop(), round_bracket_multiplier)
            elif text == "]" and len(square_brackets) > 0:
                multiply_range(square_brackets.pop(), square_bracket_multiplier)
            else:
                parts = re.split(cls.re_break, text)
                for i, part in enumerate(parts):
                    if i > 0:
                        res.append(["BREAK", -1])
                    res.append([part, 1.0])

        for pos in round_brackets:
            multiply_range(pos, round_bracket_multiplier)

        for pos in square_brackets:
            multiply_range(pos, square_bracket_multiplier)

        if len(res) == 0:
            res = [["", 1.0]]

        # merge runs of identical weights
        i = 0
        while i + 1 < len(res):
            if res[i][1] == res[i + 1][1]:
                res[i][0] += res[i + 1][0]
                res.pop(i + 1)
            else:
                i += 1

        return res

    @classmethod
    def get_token(
        cls,
        token_cls: type[TokenInterface],
        sentence: str,
        delimiter: str | None = None,
    ) -> typing.Generator[TokenInterface, None, None]:
        return (
            token_cls(text, weight)
            for text, weight in cls.parse_prompt_attention(sentence)
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
