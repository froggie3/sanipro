import typing

from sanipro.abc import TokenInterface
from sanipro.logger import logger
from sanipro.mixins import ParserPropertyMixins
from sanipro.parser import InvalidSyntaxError, NormalParser
from sanipro.parser_a1111_utils import (
    A1111ParserContext,
    A1111ParserGroupedContext,
    A1111ParserUngroupedContext,
    ParserState,
    PromptName,
    PromptWeight,
    TokenGroup,
    find_last_paren,
    parse_bad_tuple,
)

T = typing.TypeVar("T", bound=A1111ParserContext)


class A1111Parser(NormalParser, ParserPropertyMixins, typing.Generic[T]):
    ctx: T

    def is_special_char(self, char: str) -> bool:
        return char in f"\\(){self.ctx.delimiter}"

    def try_add_if_special_char_or_error(
        self, char: str, return_state: ParserState
    ) -> ParserState:
        if not self.is_special_char(char):
            raise InvalidSyntaxError("no special token was found after '\\'")
        self.ctx.prompt_name.append(char)
        return return_state

    def _handle_after_delimiter(self, char: str) -> ParserState:
        if char.isspace():
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
            index_last_paren = find_last_paren(
                self.ctx.prompt, self.ctx.current_index, self.ctx.n_parens
            )
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
        elif char.isspace():
            return ParserState.EMPHASIS_END
        else:
            self.ctx.prompt_name.clear()
            self.ctx.prompt_weight.clear()
            self.ctx.current_index = self.ctx.idx_last_delimiter
            return ParserState.PARTIAL_EMPHASIS

    def _handle_failed_parenthesis(self, char: str) -> ParserState:
        if char == "(":
            index_last_paren = find_last_paren(
                self.ctx.prompt, self.ctx.current_index, self.ctx.n_parens
            )
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
                logger.exception(
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


class A1111ParserUngrouped(A1111Parser[A1111ParserUngroupedContext]):
    def _handle_default(self, char: str) -> ParserState:
        if char == "\\":
            return ParserState.ESCAPED
        elif not char.isprintable():
            return ParserState.DEFAULT
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

    def parse_prompt(
        self, prompt: str, token_cls: type[TokenInterface], delimiter: str
    ) -> list[TokenInterface]:
        self.ctx = A1111ParserUngroupedContext(
            prompt=prompt,
            token_cls=token_cls,
            delimiter=delimiter,
            tokens=[],
            prompt_name=PromptName(),
            prompt_weight=PromptWeight(),
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


class A1111ParserGrouped(A1111Parser[A1111ParserGroupedContext]):
    def _flush_tokens(self):
        self.ctx.token_groups.append(self.ctx.tokens)
        self.ctx.tokens.clear()

    def _handle_line_break(self, char: str) -> ParserState:
        self._flush_tokens()
        return ParserState.DEFAULT

    def _handle_default(self, char: str) -> ParserState:
        if char == "\\":
            return ParserState.ESCAPED
        elif char == "\n":
            return ParserState.LINE_BREAK
        elif not char.isprintable():
            return ParserState.DEFAULT
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

    def parse_prompt(
        self, prompt: str, token_cls: type[TokenInterface], delimiter: str
    ) -> TokenGroup:
        self.ctx = A1111ParserGroupedContext(
            prompt=prompt,
            token_cls=token_cls,
            delimiter=delimiter,
            tokens=[],
            token_groups=[],
            prompt_name=PromptName(),
            prompt_weight=PromptWeight(),
            # assuming invisible delimiter would be at the start of the prompt
            idx_last_delimiter=-1,
            n_parens=0,
            current_index=0,
            state=ParserState.DEFAULT,
        )

        handlers = {
            ParserState.DEFAULT: self._handle_default,
            ParserState.LINE_BREAK: self._handle_line_break,
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

        self._flush_tokens()
        tokens = self.ctx.token_groups

        del self.ctx
        return tokens

    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
    ) -> typing.Generator[TokenInterface, None, None]:
        for tokens in self.parse_prompt(sentence, token_cls, self._delimiter.sep_input):
            for token in tokens:
                yield token
