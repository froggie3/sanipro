from . import common, filters, parser

Token = parser.TokenInteractive


def _create_pipeline_helper(separator: str) -> common.PromptPipeline:
    """Helper function to create the pipeline."""
    delimiter = common.Delimiter(",", separator)
    pipeline = delimiter.create_pipeline(common.PromptPipelineV1)

    return pipeline


def parse(
    prompt: str,
    separator=", ",
) -> common.PromptPipeline:
    pipeline = _create_pipeline_helper(separator)
    pipeline.parse(prompt, Token)

    return pipeline


def filter_example(
    prompt: str,
    separator=", ",
):
    pipeline = parse(prompt, separator)
    filter_unique = filters.UniqueCommand(reverse=True)
    pipeline.append_command(filter_unique)
    pipeline.execute(pipeline.tokens)
    return pipeline


pipeline = filter_example("aiueo")
parsed = str(pipeline)
print(parsed)


# this module offers several interfaces intended for this module to be used as a library,
# currently work in progress
