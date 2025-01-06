import re
import typing

from sanipro.abc import (
    IPromptPipeline,
    IPromptTokenizer,
    MutablePrompt,
    ParserInterface,
    TokenInterface,
)
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor
from sanipro.pipelineresult import PipelineResult


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

    def parse_prompt_attention(self, text: str) -> list[list]:
        """
        Parses a string with attention tokens and returns a list of pairs: text and its associated weight.
        Accepted tokens are:
        (abc) - increases attention to abc by a multiplier of 1.1
        (abc:3.12) - increases attention to abc by a multiplier of 3.12
        [abc] - decreases attention to abc by a multiplier of 1.1
        \\\\( - literal character '('
        \\\\[ - literal character '['
        \\\\) - literal character ')'
        \\\\] - literal character ']'
        \\\\\\ - literal character '\\\\'
        anything else - just text

        >>> parse_prompt_attention('normal text')
        [['normal text', 1.0]]
        >>> parse_prompt_attention('an (important) word')
        [['an ', 1.0], ['important', 1.1], [' word', 1.0]]
        >>> parse_prompt_attention('(unbalanced')
        [['unbalanced', 1.1]]
        >>> parse_prompt_attention('\\(literal\\]')
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

        for m in self.re_attention.finditer(text):
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
                parts = re.split(self.re_break, text)
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

    def get_token(
        self, token_cls: type[TokenInterface], sentence: str
    ) -> typing.Generator[TokenInterface, None, None]:
        return (
            token_cls(text, weight)
            for text, weight in self.parse_prompt_attention(sentence)
        )


class PromptTokenizerV2(IPromptTokenizer):
    def __init__(self, parser: ParserV2, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        return list(self._parser.get_token(self._token_cls, prompt))


class PromptPipelineV2(IPromptPipeline):
    """Automated interface."""

    _tokens: MutablePrompt
    _tokenizer: PromptTokenizerV2
    _filter_executor: IFilterExecutor

    def __init__(
        self,
        tokenizer: PromptTokenizerV2,
        filterexecutor: IFilterExecutor,
        tokens: MutablePrompt | None = None,
    ) -> None:
        if tokens is None:
            self._tokens = []
        else:
            self._tokens = tokens
        self._tokenizer = tokenizer
        self._filter_executor = filterexecutor

    def __str__(self) -> str:
        return "".join(str(token) for token in self._tokens)

    def tokenize(self, source: str) -> MutablePrompt:
        return self._tokenizer.tokenize_prompt(source)

    def execute(self, prompt: str) -> PipelineResult:
        tokenized = self._tokenizer.tokenize_prompt(prompt)
        self._tokens = self._filter_executor.execute_filter_all(tokenized)
        return PipelineResult(tokenized, self._tokens)

    def new(self, prompt: MutablePrompt):
        return type(self).__init__(self, self._tokenizer, self._filter_executor, prompt)

    @property
    def tokenizer(self) -> IPromptTokenizer:
        return self._tokenizer

    @property
    def delimiter(self) -> Delimiter:
        return Delimiter("", "")

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._tokenizer.token_cls

    @property
    def filter_executor(self) -> IFilterExecutor:
        return self._filter_executor


def create_pipeline(
    token_cls: type[TokenInterface], filt: IFilterExecutor
) -> PromptPipelineV2:
    parser = ParserV2()
    tokenizer = PromptTokenizerV2(parser=parser, token_cls=token_cls)
    pipeline = PromptPipelineV2(tokenizer=tokenizer, filterexecutor=filt)

    return pipeline
