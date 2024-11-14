from .common import Delimiter, PromptPipeline
from .parser import ParserV1, TokenInteractive


def parse(
    prompt: str,
    sep=", ",
    psr=ParserV1,
) -> PromptPipeline:
    """赤ちゃんインターフェース"""
    pipeline = PromptPipeline(
        psr,
        Delimiter(",", sep),
    )
    pipeline.execute(prompt, TokenInteractive, True)

    return pipeline


# this module offers several interfaces intended for this module to be used as a library,
# currently work in progress
