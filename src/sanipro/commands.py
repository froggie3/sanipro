import argparse
import logging
import pprint
from collections.abc import Sequence

from . import color, common, filters, sort_all_factory, utils

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


class Subcommand(object):
    """the name definition for the subcommands"""

    MASK = "mask"
    RANDOM = "random"
    SORT = "sort"
    SORT_ALL = "sort-all"
    UNIQUE = "unique"

    @classmethod
    def get_set(cls) -> set:
        ok = set([val for val in cls.__dict__.keys() if val.isupper()])
        return ok


class SaniproHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """A help formatter for this application.
    This features displaying the type name of a metavar, and the default value
    for the positional/optional arguments.

    `argparse.MetavarTypeHelpFormatter` throws a error
    when a user does not define the type of the positional/optional argument,
    which defaults to `None`. Consequently, the original module tries to get
    the attribute of `None`.

    So it seemed we could not directly inhererit the class.

    Instead, we are now implementing the same features by renewing it."""

    def _get_default_metavar_for_optional(self, action):
        metavar = action.dest.upper()
        if action.type is not None:
            return getattr(action.type, "__name__", metavar)
        return metavar

    def _get_default_metavar_for_positional(self, action):
        metavar = action.dest
        if action.type is not None:
            return getattr(action.type, "__name__", metavar)
        return metavar


class Commands(utils.HasPrettyRepr):
    # features usable in parser_v1
    mask: Sequence[str]
    random = False
    sort = False
    sort_all = False
    unique = False

    # basic functions
    exclude: Sequence[str]
    input_delimiter = ","
    interactive = False
    output_delimiter = ", "
    roundup = 2
    ps1 = f"\001{color.default}\002>>>\001{color.RESET}\002 "
    replace_to = r"%%%"
    subcommand = ""
    use_parser_v2 = False
    verbose: int | None = None

    # subcommands options
    reverse = False
    seed: int | None = None
    method = "lexicographical"

    def get_logger_level(self) -> int:
        if self.verbose is None:
            return logging.WARNING
        try:
            log_level = utils.get_log_level_from(self.verbose)
            return log_level
        except ValueError:
            raise ValueError("the maximum two -v flags can only be added")

    def debug(self) -> None:
        pprint.pprint(self, utils.get_debug_fp())

    @classmethod
    def prepare_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="sanipro",
            description=(
                "Toolbox for Stable Diffusion prompts. "
                "'Sanipro' stands for 'pro'mpt 'sani'tizer."
            ),
            formatter_class=SaniproHelpFormatter,
            epilog="Helps for subcommands are available, respectively.",
        )

        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            help=(
                "Switch to display the extra logs for nerds, "
                "This may be useful for debugging. Adding more flags causes your terminal more messier."
            ),
        )

        parser.add_argument(
            "-d",
            "--input-delimiter",
            type=str,
            default=cls.input_delimiter,
            help=("Preferred delimiter string for the original prompts. " ""),
        )

        parser.add_argument(
            "-s",
            "--output-delimiter",
            default=cls.output_delimiter,
            type=str,
            help=("Preferred delimiter string for the processed prompts. " ""),
        )

        parser.add_argument(
            "-p",
            "--ps1",
            default=cls.ps1,
            type=str,
            help=(
                "The custom string that is used to wait for the user input "
                "of the prompts."
            ),
        )

        parser.add_argument(
            "-i",
            "--interactive",
            default=cls.interactive,
            action="store_true",
            help=(
                "Provides the REPL interface to play with prompts. "
                "The program behaves like the Python interpreter."
            ),
        )

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

        subparsers = parser.add_subparsers(
            title="Subcommands",
            description=(
                "List of available filters that can be applied to the prompt. "
                "Just one filter can be applied at once."
            ),
            dest="subcommand",
            metavar="Filters",
        )

        parser_mask = subparsers.add_parser(
            Subcommand.MASK,
            help="Mask tokens with words.",
            description="Mask words specified with another word (optional).",
            epilog=(
                (
                    "Note that you can still use the global `--exclude` option"
                    "as well as this filter."
                )
            ),
        )

        parser_mask.add_argument("mask", nargs="*", type=str, help="Masks this word.")

        parser_mask.add_argument(
            "-t",
            "--replace-to",
            type=str,
            default=cls.replace_to,
            help="The new character or string replaced to.",
        )

        parser_random = subparsers.add_parser(
            Subcommand.RANDOM,
            help="Shuffles all the prompts altogether.",
            description="Shuffles all the prompts altogether.",
        )

        parser_random.add_argument(
            "-b",
            "--seed",
            default=cls.seed,
            type=int,
            help="Fixed randomness to this value.",
        )

        parser_sort = subparsers.add_parser(
            Subcommand.SORT,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )
        parser_sort.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )

        parser_sort_all = subparsers.add_parser(
            Subcommand.SORT_ALL,
            help="Reorders all the prompts.",
            description="Reorders all the prompts.",
            epilog="METHOD = { " + ", ".join(sort_all_factory.available) + " }",
        )

        parser_sort_all.add_argument(
            "-m",
            "--method",
            default=cls.method,
            const=cls.method,
            type=str,
            nargs="?",
            help="Based on this strategy.",
        )

        parser_sort_all.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )

        parser_unique = subparsers.add_parser(
            Subcommand.UNIQUE,
            help="Removes duplicated tokens, and uniquify them.",
            description="Removes duplicated tokens, and uniquify them.",
            epilog="",
        )

        parser_unique.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="Make the token with the heaviest weight survived.",
        )

        return parser

    @property
    def get_delimiter(self) -> common.Delimiter:
        return common.Delimiter(self.input_delimiter, self.output_delimiter)

    def get_pipeline_from(self, use_parser_v2: bool) -> common.PromptPipeline:
        delim = self.get_delimiter
        if not use_parser_v2:
            return delim.create_pipeline(common.PromptPipelineV1)
        return delim.create_pipeline(common.PromptPipelineV2)

    def get_pipeline(self) -> common.PromptPipeline:
        if self.use_parser_v2 and self.subcommand in Subcommand.get_set():
            raise NotImplementedError(
                f"the '{self.subcommand}' command is not available "
                "when using parse_v2."
            )

        if self.use_parser_v2:
            logger.warning("using parser_v2.")

        pipeline = self.get_pipeline_from(self.use_parser_v2)
        # always round
        pipeline.append_command(filters.RoundUpCommand(self.roundup))

        if self.subcommand == Subcommand.RANDOM:
            pipeline.append_command(filters.RandomCommand(self.seed))

        if self.subcommand == Subcommand.SORT_ALL:
            sorted_partial = sort_all_factory.apply_from(self.method)
            pipeline.append_command(
                filters.SortAllCommand(sorted_partial, self.reverse)
            )

        if self.subcommand == Subcommand.SORT:
            pipeline.append_command(filters.SortCommand(self.reverse))

        if self.subcommand == Subcommand.UNIQUE:
            pipeline.append_command(filters.UniqueCommand(self.reverse))

        if self.subcommand == Subcommand.MASK:
            pipeline.append_command(filters.MaskCommand(self.mask, self.replace_to))

        if self.exclude:
            pipeline.append_command(filters.ExcludeCommand(self.exclude))

        return pipeline

    @classmethod
    def from_sys_argv(cls, arg_val: Sequence) -> "Commands":
        parser = cls.prepare_parser()
        args = parser.parse_args(arg_val, namespace=cls())

        return args
