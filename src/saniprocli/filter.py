import argparse
import functools
import logging

from sanipro.compatible import Self
from sanipro.filters import (
    exclude,
    fuzzysort,
    mask,
    random,
    reset,
    roundup,
    sort,
    sort_all,
    unique,
)
from sanipro.filters.abc import ReordererStrategy
from sanipro.utils import CommandModuleMap, KeyVal, ModuleMatcher
from saniprocli import cli_demo
from saniprocli.help_formatter import SaniproHelpFormatter

logger = logging.getLogger(__name__)


class ExcludeCommand(exclude.ExcludeCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        pass


class SimilarCommand(fuzzysort.SimilarCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subparser_similar = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Reorders tokens with their similarity.",
            description="Reorders tokens with their similarity.",
        )

        subparser_similar.add_argument(
            "-r",
            "--reverse",
            default=False,
            action="store_true",
            help="With reversed order.",
        )

        subcommand = subparser_similar.add_subparsers(
            title=cls.command_id,
            help="With what method is used to reorder the tokens.",
            description="Reorders tokens with their similarity.",
            dest="similar_method",
            metavar="METHOD",
        )

        subcommand.add_parser(
            Available.NAIVE.key,
            formatter_class=SaniproHelpFormatter,
            help=(
                "Calculates all permutations of a sequence of tokens. "
                "Not practical at all."
            ),
        )

        subcommand.add_parser(
            Available.GREEDY.key,
            formatter_class=SaniproHelpFormatter,
            help=(
                "Uses a greedy approach that always chooses the next element "
                "with the highest similarity."
            ),
        )

        mst_parser = subcommand.add_parser(
            "mst",
            formatter_class=SaniproHelpFormatter,
            help=("Construct a complete graph with tokens as vertices."),
            description=(
                "Construct a complete graph with tokens as vertices "
                "and similarities as edge weights."
            ),
        )

        mst_group = mst_parser.add_mutually_exclusive_group()

        mst_group.add_argument(
            "-k", "--kruskal", action="store_true", help=("Uses Kruskal's algorithm.")
        )

        mst_group.add_argument(
            "-p", "--prim", action="store_true", help=("Uses Prim's algorithm.")
        )

    @staticmethod
    def get_reorderer(cmd: "cli_demo.DemoCommands") -> ReordererStrategy:
        """Instanciate one reorder function from the parsed result."""

        def get_class(cmd: "cli_demo.DemoCommands"):
            query = cmd.similar_method
            if query != "mst":
                return fuzzysort_apply_from(method=query)

            adapters = [[cmd.kruskal, Available.KRUSKAL], [cmd.prim, Available.PRIM]]
            for _flag, _cls in adapters:
                if _flag:
                    # when --kruskal or --prim flag is specified
                    return _cls.val

            _, fallback_cls = adapters[0]
            return fallback_cls.val

        cls = get_class(cmd)
        logger.debug(f"selected module: {cls.__name__}")

        if cls is None:
            raise KeyError

        return cls(strategy=fuzzysort.SequenceMatcherSimilarity())

    @classmethod
    def create_from_cmd(cls, cmd: "cli_demo.DemoCommands", *, reverse=False) -> Self:
        """Alternative method."""
        return cls(reorderer=cls.get_reorderer(cmd), reverse=reverse)


class Available(CommandModuleMap):
    NAIVE = KeyVal("naive", fuzzysort.NaiveReorderer)
    GREEDY = KeyVal("greedy", fuzzysort.GreedyReorderer)
    KRUSKAL = KeyVal("kruskal", fuzzysort.KruskalMSTReorderer)
    PRIM = KeyVal("prim", fuzzysort.PrimMSTReorderer)


def fuzzysort_apply_from(*, method: str | None = None) -> type[fuzzysort.MSTReorderer]:
    """
    method を具体的なクラスの名前にマッチングさせる。

    Argument:
        method: コマンドラインで指定された方法.
    """
    # set default
    default = Available.GREEDY.key
    if method is None:
        method = default

    mapper = ModuleMatcher(Available)
    try:
        return mapper.match(method)
    except KeyError:
        raise ValueError("method name is not found.")


class MaskCommand(mask.MaskCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            help="Mask tokens with words.",
            description="Mask words specified with another word (optional).",
            formatter_class=SaniproHelpFormatter,
            epilog=(
                (
                    "Note that you can still use the global `--exclude` option"
                    "as well as this filter."
                )
            ),
        )

        subcommand.add_argument("mask", nargs="*", type=str, help="Masks this word.")

        subcommand.add_argument(
            "-t",
            "--replace-to",
            type=str,
            default=r"%%%",
            help="The new character or string replaced to.",
        )


class RandomCommand(random.RandomCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Shuffles all the prompts altogether.",
            description="Shuffles all the prompts altogether.",
        )

        subcommand.add_argument(
            "-b",
            "--seed",
            default=None,
            type=int,
            help="Fixed randomness to this value.",
        )


class ResetCommand(reset.ResetCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Initializes all the weight of the tokens.",
            description="Initializes all the weight of the tokens.",
        )

        subcommand.add_argument(
            "-v",
            "--value",
            default=1.0,
            type=float,
            help="Fixes the weight to this value.",
        )


class RoundUpCommand(roundup.RoundUpCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction): ...


class SortCommand(sort.SortCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )

        subcommand.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )


def sort_all_apply_from(*, method: str | None = None) -> functools.partial:
    """
    method を具体的なクラスの名前にマッチングさせる。

    Argument:
        method: コマンドラインで指定された方法.
    """
    # set default
    default = sort_all.Available.LEXICOGRAPHICAL.key
    if method is None:
        method = default

    mapper = ModuleMatcher(sort_all.Available)
    try:
        partial = functools.partial(sorted, key=mapper.match(method))
        return partial
    except KeyError:
        raise ValueError("method name is not found.")


class SortAllCommand(sort_all.SortAllCommand):
    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        sort_all_subparser = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Reorders all the prompts.",
            description="Reorders all the prompts.",
        )

        sort_all_subparser.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )

        subcommand = sort_all_subparser.add_subparsers(
            title=cls.command_id,
            description="The available method to sort the tokens.",
            dest="sort_all_method",
            metavar="METHOD",
        )

        subcommand.add_parser(
            sort_all.Available.LEXICOGRAPHICAL.key,
            help="Sort the prompt with lexicographical order. Familiar sort method.",
        )

        subcommand.add_parser(
            sort_all.Available.LENGTH.key,
            help=(
                "Reorder the token length."
                "This behaves slightly similar as 'ord-sum' method."
            ),
        )

        subcommand.add_parser(
            sort_all.Available.STRENGTH.key, help="Reorder the tokens by their weights."
        )

        subcommand.add_parser(
            sort_all.Available.ORD_SUM.key,
            help=(
                "Reorder the tokens by its sum of character codes."
                "This behaves slightly similar as 'length' method."
            ),
        )

    @classmethod
    def create_from_cmd(cls, cmd: "cli_demo.DemoCommands", *, reverse=False) -> Self:
        """Alternative method."""
        partial = sort_all_apply_from(method=cmd.sort_all_method)
        return cls(partial, reverse=reverse)


class UniqueCommand(unique.UniqueCommand):

    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subparser_unique = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Removes duplicated tokens, and uniquify them.",
            description="Removes duplicated tokens, and uniquify them.",
            epilog="",
        )

        subparser_unique.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="Make the token with the heaviest weight survived.",
        )
