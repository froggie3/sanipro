from .common import Delimiter, PromptBuilder
from .parser import Parser, ParserV1, TokenInteractive


def parse(
    prompt: str,
    sep=", ",
    psr=ParserV1,
) -> PromptBuilder:
    """赤ちゃんインターフェース"""
    builder = PromptBuilder(
        psr,
        Delimiter(",", sep),
    )
    builder.parse(prompt, TokenInteractive, True)

    return builder


# this module offers several interfaces intended for this module to be used as a library,
# currently work in progress
