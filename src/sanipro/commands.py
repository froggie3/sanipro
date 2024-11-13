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


class Commands(utils.HasPrettyRepr):
    # features usable in parser_v1
    mask = False
    random = False
    sort = False
    sort_all = False
    unique = False

    # basic functions
    exclude = False
    input_delimiter = ","
    interactive = False
    output_delimiter = ", "
    roundup = 2
    ps1 = f"{color.default}>>>{color.RESET} "
    replace_to = r"%%%"
    subcommand = ""
    use_parser_v2 = False
    verbose: int | None = None

    # subcommands options
    reverse = False
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
        pprint.pprint(self, utils.debug_fp)

    @classmethod
    def prepare_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="sanipro",
            description=(
                "Toolbox for Stable Diffusion prompts. "
                "'Sanipro' stands for 'pro'mpt 'sani'tizer."
            ),
            epilog="Helps for subcommands are available, respectively.",
        )

        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            help=(
                "Switch to display the extra logs for nerds, "
                "This may be useful for debugging."
            ),
        )

        parser.add_argument(
            "-d",
            "--input-delimiter",
            metavar="str",
            default=cls.input_delimiter,
            help=(
                "Preferred delimiter string for the original prompts. "
                "(default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-s",
            "--output-delimiter",
            metavar="str",
            default=cls.output_delimiter,
            help=(
                "Preferred delimiter string for the processed prompts. "
                "(default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-p",
            "--ps1",
            metavar="str",
            default=cls.ps1,
            help=(
                "Custom string that is used when asking user "
                "for the prompts (default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Provides REPL interface to play with prompts.",
        )

        parser.add_argument(
            "-u",
            "--roundup",
            metavar="n",
            default=cls.roundup,
            type=int,
            help=(
                "All the token with weights (> 1.0 or < 1.0) "
                "will be rounded up to n digit(s) in here (default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-x",
            "--exclude",
            metavar="str",
            nargs="*",
            help=(
                "Exclude this token from original prompt. "
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
                "List of available filters that can be applied to the prompt."
            ),
            dest="subcommand",
            help=("Just one filter can be applied at once."),
            metavar="FILTER",
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

        parser_mask.add_argument(
            "mask",
            nargs="*",
            help="Masks this word.",
        )

        parser_mask.add_argument(
            "-t",
            "--replace-to",
            default=cls.replace_to,
            help="The new character or string replaced to.",
        )

        parser_random = subparsers.add_parser(
            Subcommand.RANDOM,
            help="Shuffles all the prompts altogether.",
            description="Shuffles all the prompts altogether.",
        )

        parser_sort = subparsers.add_parser(
            Subcommand.SORT,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )
        parser_sort.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="With reversed order.",
        )

        parser_sort_all = subparsers.add_parser(
            Subcommand.SORT_ALL,
            help="Reorder all the prompts.",
            description="Reorder all the prompts.",
            epilog="METHOD = { " + ", ".join(sort_all_factory.available) + " }",
        )

        parser_sort_all.add_argument(
            "-m",
            "--method",
            default=cls.method,
            const=cls.method,
            nargs="?",
            help="Based on this strategy (default: `%(default)s`)",
        )

        parser_sort_all.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="With reversed order.",
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
        return common.Delimiter(
            self.input_delimiter,
            self.output_delimiter,
        )

    def get_builder_from(self, use_parser_v2: bool) -> common.PromptBuilder:
        delim = self.get_delimiter
        if not use_parser_v2:
            return delim.create_builder(common.PromptBuilderV1)
        return delim.create_builder(common.PromptBuilderV2)

    def get_builder(self) -> common.PromptBuilder:
        cfg = common.FuncConfig

        if self.use_parser_v2 and self.subcommand in Subcommand.get_set():
            raise NotImplementedError(
                f"the '{self.subcommand}' command is not available "
                "when using parse_v2."
            )

        if self.use_parser_v2:
            logger.warning("using parser_v2.")

        builder = self.get_builder_from(self.use_parser_v2)
        # always round
        builder.append_hook(
            cfg(
                func=filters.round_up,
                kwargs={"digits": self.roundup},
            ),
        )

        if self.subcommand == Subcommand.RANDOM:
            builder.append_hook(
                cfg(
                    func=filters.random,
                    kwargs={},
                ),
            )

        if self.subcommand == Subcommand.SORT_ALL:
            sorted_partial = sort_all_factory.apply_from(self.method)
            builder.append_hook(
                cfg(
                    func=filters.sort_all,
                    kwargs={
                        "sorted_partial": sorted_partial,
                        "reverse": True if (self.reverse or False) else False,
                    },
                )
            )

        if self.subcommand == Subcommand.SORT:
            builder.append_hook(
                cfg(
                    func=filters.sort,
                    kwargs={
                        "reverse": (self.reverse or False),
                    },
                )
            )

        if self.subcommand == Subcommand.UNIQUE:
            builder.append_hook(
                cfg(
                    func=filters.unique,
                    kwargs={
                        "reverse": self.reverse or False,
                    },
                )
            )

        if self.subcommand == Subcommand.MASK:
            builder.append_hook(
                cfg(
                    func=filters.mask,
                    kwargs={
                        "excludes": self.mask,
                        "replace_to": self.replace_to,
                    },
                )
            )

        if self.exclude:
            builder.append_hook(
                cfg(
                    func=filters.exclude,
                    kwargs={
                        "excludes": self.exclude,
                    },
                ),
            )

        return builder

    @classmethod
    def from_sys_argv(cls, arg_val: Sequence) -> "Commands":
        parser = cls.prepare_parser()
        args = parser.parse_args(arg_val, namespace=cls())

        return args
