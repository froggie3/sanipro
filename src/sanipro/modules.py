from .common import Delimiter, PromptBuilder
from .parser import TokenInteractive


def parse(prompt: str, sep=", ") -> PromptBuilder:
    """赤ちゃんインターフェース"""
    builder = PromptBuilder(Delimiter(",", sep))
    builder.parse(prompt, TokenInteractive, True)

    return builder


# this module offers several interfaces intended for this module to be used as a library,
# currently work in progress
