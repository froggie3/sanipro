import argparse
import logging

from sanipro import fuzzysort
from sanipro.abc import MutablePrompt, Prompt
from sanipro.help_formatter import SaniproHelpFormatter

from .. import fuzzysort
from . import commands
from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


class SimilarCommand(Command):
    def __init__(self, reorderer: fuzzysort.ReordererStrategy, *, reverse=False):
        self.reorderer = reorderer
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        sorted_words_seq = self.reorderer.find_optimal_order(prompt)
        return (
            sorted_words_seq if not self.reverse else list(reversed(sorted_words_seq))
        )

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subparser_similar = subparser.add_parser(
            Filter.SIMILAR,
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
            title=Filter.SIMILAR,
            help="With what method is used to reorder the tokens.",
            description="Reorders tokens with their similarity.",
            dest="similar_method",
            metavar="METHOD",
        )

        subcommand.add_parser(
            fuzzysort.Available.NAIVE.key,
            formatter_class=SaniproHelpFormatter,
            help=(
                "Calculates all permutations of a sequence of tokens. "
                "Not practical at all."
            ),
        )

        subcommand.add_parser(
            fuzzysort.Available.GREEDY.key,
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
    def get_instance(cmd: "commands.Commands") -> fuzzysort.ReordererStrategy:
        """Instanciate one reorder function from the parsed result."""

        def get_class(cmd: "commands.Commands"):
            query = cmd.similar_method
            if query != "mst":
                return fuzzysort.apply_from(method=query)

            adapters = [
                [cmd.kruskal, fuzzysort.Available.KRUSKAL],
                [cmd.prim, fuzzysort.Available.PRIM],
            ]
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
