import sanipro.delimiter
from sanipro import parser
from sanipro.delimiter import Delimiter
from sanipro.filters.unique import UniqueCommand
from sanipro.pipeline import PromptPipeline, PromptPipelineV1, PromptPipelineV2

Token = parser.TokenInteractive

"""
this module offers several interfaces intended for this module to be used as a library,
currently work in progress
"""


def create_pipeline(delimiter: Delimiter, cls: type[PromptPipeline]) -> PromptPipeline:
    """Creates pipeline."""
    pipe = None
    if cls is PromptPipelineV1:
        pipe = cls(parser.ParserV1, delimiter)
    elif cls is PromptPipelineV2:
        pipe = cls(parser.ParserV2, delimiter)
    if pipe is not None:
        return pipe

    raise ValueError(
        f"failed to match the {cls.__name__} class with any of {PromptPipeline.__name__}"
    )


def _create_pipeline_helper(separator: str) -> PromptPipeline:
    """Helper function to create the pipeline."""
    delimiter = sanipro.delimiter.Delimiter(",", separator)
    pipeline = create_pipeline(delimiter, PromptPipelineV1)

    return pipeline


def parse(prompt: str, separator=", ") -> PromptPipeline:
    pipeline = _create_pipeline_helper(separator)
    pipeline.parse(prompt, Token)

    return pipeline


def filter_example(prompt: str, separator=", "):
    pipeline = parse(prompt, separator)
    filter_unique = UniqueCommand(reverse=True)
    pipeline.append_command(filter_unique)
    pipeline.execute(pipeline.tokens)
    return pipeline


if __name__ == "__main__":
    pipeline = filter_example("aiueo")
    parsed = str(pipeline)
    print(parsed)
