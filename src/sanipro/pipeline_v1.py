import re
import typing

from sanipro.abc import IPromptPipeline, IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor
from sanipro.parser import NormalParser
from sanipro.pipelineresult import PipelineResult


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


class ParserV1(NormalParser):
    @staticmethod
    def parse_prompt(
        prompt: str, token_cls: type[TokenInterface], delimiter: str
    ) -> list[TokenInterface]:
        """
        split `token_combined` into left and right sides with `:`
        when there are three or more elements,
        the right side separated by the last colon is adopted as the weight.
        """

        tokens = []
        prompt_name = []
        prompt_weight = []
        idx_last_delimiter = 0
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
                    pass
                elif char == delimiter:  # prompt was ended without emphasis.
                    prompt_name_concat = "".join(prompt_name).strip()
                    prompt_name.clear()
                    tokens.append(token_cls(prompt_name_concat, 1.0))
                    idx_last_delimiter = i + 1
                else:
                    prompt_name.append(char)

            elif m_general == 10:  # in escaped
                prompt_name.append(char)
                m_general = 00

            elif m_general == 11:  # in parenthesis, and escaped
                prompt_name.append(char)
                m_general = 20

            elif m_general == 20:  # in parenthesis
                if char == "\\":
                    prompt_name.append(char)
                    m_general = 11
                elif char == ":":
                    m_general = 30
                elif char == "(":
                    index_last_paren = find_last_paren(prompt, i, n_parens)
                    tmp_buffer = prompt[i : index_last_paren + 1]
                    prompt_name.extend(tmp_buffer)

                    i = index_last_paren
                elif char == ")":
                    raise ValueError(
                        "the emphasis syntax in a1111 requires a value after a colon"
                    )
                else:
                    prompt_name.append(char)

            elif m_general == 30:  # after a colon
                if char == ")":
                    m_general = 50
                    n_parens -= 1
                else:
                    prompt_weight.append(char)

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
                else:
                    prompt_name.clear()
                    prompt_weight.clear()
                    i = idx_last_delimiter - 1
                    m_general = 100

            elif (
                m_general == 100
            ):  # token contains partial emphasis (e.g. "(bba:1.2) aba")
                if char == "\\":
                    prompt_name.append(char)
                    m_general = 110
                elif char == delimiter:  # prompt was ended without emphasis.
                    prompt_name_concat = "".join(prompt_name).strip()
                    prompt_name.clear()
                    tokens.append(token_cls(prompt_name_concat, 1.0))
                    idx_last_delimiter = i + 1
                    m_general = 00
                else:
                    prompt_name.append(char)

            elif m_general == 110:  # in escaped
                prompt_name.append(char)
                m_general = 100

            i += 1
        return tokens

    def delete_colon(self, s: str) -> str:
        re_pattern = re.compile(r"\\:")
        return re.sub(re_pattern, ":", s)

    def _postprocess(self, token: TokenInterface) -> TokenInterface:
        name_new = self.delete_colon(token.name)
        token = token.replace(new_name=name_new)
        return token

    def get_token(
        self, token_cls: type[TokenInterface], sentence: str
    ) -> typing.Generator[TokenInterface, None, None]:
        for token in self.parse_prompt(sentence, token_cls, self._delimiter.sep_input):
            yield self._postprocess(token)


class PromptTokenizerV1(IPromptTokenizer):
    def __init__(self, parser: NormalParser, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def _strip_last_break(self, prompt: str) -> str:
        """Strip last line break."""

        return prompt.strip()

    def _escape_colons(self, prompt: str, sep: str) -> str:
        """Escape colons."""

        re_pattern = re.compile(r":(?!\d+(?:\.\d+)?)")
        return sep.join(re.sub(re_pattern, r"\:", token) for token in prompt.split(sep))

    def _add_last_comma(self, prompt: str, sep: str) -> str:
        """Adds a comma to the prompt at the last."""

        if not prompt.endswith(sep):
            prompt += sep
        return prompt

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        prompt = self._preprocess(prompt)
        return list(self._parser.get_token(self._token_cls, prompt))

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls

    def _preprocess(self, prompt: str) -> str:
        """Some preprocesses for ease of implementation."""

        delim = self._parser._delimiter.sep_input
        prompt = self._strip_last_break(prompt)
        prompt = self._escape_colons(prompt, delim)
        prompt = self._add_last_comma(prompt, delim)

        return prompt


class PromptPipelineV1(IPromptPipeline):
    """Automated interface."""

    _tokens: MutablePrompt
    _tokenizer: PromptTokenizerV1
    _filter_executor: IFilterExecutor

    def __init__(
        self,
        tokenizer: PromptTokenizerV1,
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
        delim = self._tokenizer._parser._delimiter.sep_output
        return delim.join(str(token) for token in self._tokens)

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
        return self._tokenizer._parser._delimiter

    @property
    def filter_executor(self) -> IFilterExecutor:
        return self._filter_executor


def create_pipeline(
    sepin: str, sepout: str, token_cls: type[TokenInterface], filt: IFilterExecutor
) -> PromptPipelineV1:
    delimiter = Delimiter(sepin, sepout)
    parser = ParserV1(delimiter=delimiter)
    tokenizer = PromptTokenizerV1(parser=parser, token_cls=token_cls)
    pipeline = PromptPipelineV1(tokenizer=tokenizer, filterexecutor=filt)

    return pipeline
