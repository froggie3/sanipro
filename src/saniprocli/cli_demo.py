import argparse
import logging
from collections.abc import Sequence

from sanipro import common
from saniprocli.commands import Commands
from saniprocli.filter import (
    ExcludeCommand,
    MaskCommand,
    RandomCommand,
    ResetCommand,
    RoundUpCommand,
    SimilarCommand,
    SortAllCommand,
    SortCommand,
    UniqueCommand,
)

logger_root = logging.getLogger()

logger = logging.getLogger(__name__)


class DemoCommands(Commands):
    """Custom subcommand implementation by user"""

    # global options
    exclude: Sequence[str]
    roundup = 2
    replace_to = ""
    mask: Sequence[str]
    use_parser_v2 = False

    # subcommands options
    reverse = False
    seed: int | None = None
    value: float | None = None
    similar_method = None
    sort_all_method = None
    kruskal = None
    prim = None

    command_classes = (
        MaskCommand,
        RandomCommand,
        ResetCommand,
        SimilarCommand,
        SortAllCommand,
        SortCommand,
        UniqueCommand,
    )

    @classmethod
    def append_parser(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-u",
            "--roundup",
            default=cls.roundup,
            type=int,
            help=(
                "All the token with weights (x > 1.0 or x < 1.0) "
                "will be rounded up to n digit(s)."
            ),
        )

        parser.add_argument(
            "-x",
            "--exclude",
            type=str,
            nargs="*",
            help=(
                "Exclude this token from the original prompt. "
                "Multiple options can be specified."
            ),
        )

        parser.add_argument(
            "--use-parser-v2",
            "-2",
            action="store_true",
            help=(
                "Switch to use another version of the parser instead. "
                "This might be inferrior to the default parser "
                "as it only parses the prompt and does nothing at all."
            ),
        )

    @classmethod
    def append_subparser(cls, parser: argparse.ArgumentParser) -> None:
        subparser = parser.add_subparsers(
            title="filter",
            description=(
                "List of available filters that can be applied to the prompt. "
                "Just one filter can be applied at once."
            ),
            dest="filter",
            metavar="FILTER",
        )

        for cmd in cls.command_classes:
            cmd.inject_subparser(subparser)

    def _get_pipeline_from(self, use_parser_v2: bool) -> common.PromptPipeline:
        delimiter = common.Delimiter(self.input_delimiter, self.output_delimiter)
        pipeline = None
        if not use_parser_v2:
            pipeline = delimiter.create_pipeline(common.PromptPipelineV1)
        else:
            pipeline = delimiter.create_pipeline(common.PromptPipelineV2)
        return pipeline

    def get_pipeline(self) -> common.PromptPipeline:
        """This is a pipeline for the purpose of showcasing.
        Since all the parameters of each command is variable, the command
        sacrifies the composability.
        It is good for you to create your own pipeline, and name it
        so you can use it as a preset."""

        command_ids = [cmd.command_id for cmd in self.command_classes]
        command_funcs = (
            lambda: MaskCommand(self.mask, self.replace_to),
            lambda: RandomCommand(self.seed),
            lambda: ResetCommand(self.value),
            lambda: SimilarCommand.create_from_cmd(cmd=self, reverse=self.reverse),
            lambda: SortAllCommand.create_from_cmd(cmd=self, reverse=self.reverse),
            lambda: SortCommand(self.reverse),
            lambda: UniqueCommand(self.reverse),
        )
        command_map = dict(zip(command_ids, command_funcs, strict=True))

        if self.use_parser_v2:
            if self.filter in command_ids:
                raise NotImplementedError(
                    f"the '{self.filter}' command is not available "
                    "when using parse_v2."
                )

            logger.warning("using parser_v2.")

        pipeline = self._get_pipeline_from(self.use_parser_v2)

        # always round
        pipeline.append_command(RoundUpCommand(self.roundup))

        if self.filter is not None:
            lambd = command_map[self.filter]
            pipeline.append_command(lambd())

        if self.exclude:
            pipeline.append_command(ExcludeCommand(self.exclude))

        return pipeline
