import argparse
import collections
import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from functools import partial
from itertools import chain

from . import fuzzysort, sort_all, utils
from .abc import MutablePrompt, Prompt, TokenInterface
from .help_formatter import SaniproHelpFormatter

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    def execute(self, prompt: Prompt) -> MutablePrompt: ...

    @staticmethod
    @abstractmethod
    def inject_subparser(subparser: argparse._SubParsersAction): ...


def collect_same_tokens(prompts: Prompt) -> Mapping[str, MutablePrompt]:
    groups = collections.defaultdict(list)
    for prompt in prompts:
        groups[prompt.name].append(prompt)
    return groups


def collect_same_tokens_sorted(
    prompt: Prompt, reverse=False
) -> typing.Generator[list[TokenInterface], None, None]:
    f = sort_all.sort_by_strength
    return (
        sorted(token, key=f, reverse=reverse)
        for token in collect_same_tokens(prompt).values()
    )


class MaskCommand(Command):
    def __init__(self, excludes: Sequence[str], replace_to: str):
        self.excludes = excludes
        self.replace_to = replace_to

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['%%%', 'thighhighs']
        """
        return [
            token.replace(self.replace_to) if token.name in self.excludes else token
            for token in prompt
        ]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.MASK,
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


class ExcludeCommand(Command):
    def __init__(self, excludes: Sequence[str]):
        self.excludes = excludes

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['thighhighs']
        """
        return [token for token in prompt if token.name not in self.excludes]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        pass


class SortAllCommand(Command):
    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        sort_all_subparser = subparser.add_parser(
            Filter.SORT_ALL,
            formatter_class=SaniproHelpFormatter,
            help="Reorders all the prompts.",
            description="Reorders all the prompts.",
        )

        sort_all_subparser.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )

        subcommand = sort_all_subparser.add_subparsers(
            title=Filter.SORT_ALL,
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


class RoundUpCommand(Command):
    def __init__(self, digits: int):
        self.digits = digits

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return [utils.round_token_weight(token, self.digits) for token in prompt]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction): ...


class RandomCommand(Command):
    def __init__(self, seed: int | None = None):
        self.seed = seed

    def execute(self, prompt: Prompt) -> MutablePrompt:
        if self.seed is not None:
            random.seed(self.seed)

        if not isinstance(prompt, typing.MutableSequence):
            _prompt = random.sample(prompt, len(prompt))
            return _prompt

        random.shuffle(prompt)
        return prompt

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.RANDOM,
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


class SortCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.0), ('white hair', 1.2)]

        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.2), ('white hair', 1.0)]
        """
        return list(chain(*collect_same_tokens_sorted(prompt, self.reverse)))

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.SORT,
            formatter_class=SaniproHelpFormatter,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )

        subcommand.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )


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


class UniqueCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.0)]

        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.2)]
        """
        return [vals[0] for vals in collect_same_tokens_sorted(prompt, self.reverse)]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subparser_unique = subparser.add_parser(
            Filter.UNIQUE,
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


class Filter(utils.CommandModuleMap):
    MASK = "mask"
    RANDOM = "random"
    SORT = "sort"
    SORT_ALL = "sort-all"
    SIMILAR = "similar"
    UNIQUE = "unique"


if __name__ == "__main__":
    import doctest

    doctest.testmod()
