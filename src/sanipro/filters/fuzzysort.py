import argparse
import itertools
import logging
import random
from difflib import SequenceMatcher

import networkx as nx
from networkx import traversal

from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.commandline import commands
from sanipro.commandline.help_formatter import SaniproHelpFormatter
from sanipro.utils import CommandModuleMap, KeyVal, ModuleMatcher

from .abc import Command, MSTBuilder, ReordererStrategy, SimilarityStrategy

logger = logging.getLogger(__name__)


try:
    import Levenshtein  # type: ignore

    class LevenshteinSimilarity(SimilarityStrategy):
        """Levenshtein距離を利用した類似度計算"""

        def calculate_similarity(self, word1: str, word2: str) -> float:
            distance = Levenshtein.distance(word1, word2)
            max_len = max(len(word1), len(word2))
            return 1 - (distance / max_len)

except ImportError:
    pass


class SequenceMatcherSimilarity(SimilarityStrategy):
    """SequenceMatcherを利用した類似度計算"""

    def calculate_similarity(self, word1: str, word2: str) -> float:
        return SequenceMatcher(None, word1, word2).ratio()


class NaiveReorderer(ReordererStrategy):
    """トークンの配列の全順列を試し、類似度順に並べ替えを行うクラス"""

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        best_order = tuple()
        best_score = float("-inf")

        # 全順列を試して最もスコアが高い順序を見つける
        for permutation in itertools.permutations(words):
            total_score = sum(
                self.strategy.calculate_similarity(
                    permutation[i].name, permutation[i + 1].name
                )
                for i in range(len(permutation) - 1)
            )
            if total_score > best_score:
                best_score = total_score
                best_order = permutation

        return list(best_order)


class GreedyReorderer(ReordererStrategy):
    """貪欲法による並べ替えを試行する。"""

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def _find_max_idx(
        self, last_word: str, words: list[TokenInterface], visited: list[bool]
    ) -> int | None:
        tmp = float("-inf")
        idx = None

        for i, w in enumerate(words):
            if visited[i]:
                continue
            similarity = self.strategy.calculate_similarity(last_word, w.name)
            if similarity > tmp:
                tmp = similarity
                idx = i

        return idx

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        # シャッフルしてランダムな初期要素を選ぶ
        words = list(words[:])
        random.shuffle(words)
        result = [words.pop()]
        visited = [False] * len(words)

        # 貪欲法で最も似ている単語を選び続ける
        while True:
            last_word = result[-1].name
            next_idx = self._find_max_idx(last_word, words, visited)

            # 探索しても見つからない場合は全部探索しきったということなので
            if next_idx is None:
                break

            result.append(words[next_idx])
            visited[next_idx] = True

        return result


class PrimMSTBuilder(MSTBuilder):
    def build_mst(self, graph: nx.Graph) -> nx.Graph:
        return nx.minimum_spanning_tree(graph, algorithm="prim")


class KruskalMSTBuilder(MSTBuilder):
    def build_mst(self, graph: nx.Graph) -> nx.Graph:
        return nx.minimum_spanning_tree(graph)


import itertools


class MSTReorderer(ReordererStrategy):
    """最小全域木による並べ替え戦略"""

    mst_builder: MSTBuilder

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        # 完全グラフのエッジリストを構築
        graph = nx.Graph()

        for (u, _p), (v, _q) in itertools.combinations(enumerate(words), 2):
            similarity = self.strategy.calculate_similarity(_p.name, _q.name)
            # 類似度が高いほど重みは低くする
            graph.add_edge(u, v, weight=1 - similarity)

        # MSTを構築
        mst = self.mst_builder.build_mst(graph)

        # 最小全域木をDFSで探索し、順序を決定
        def mapper(node: int):
            token = words[node]
            return token

        order = map(mapper, traversal.dfs_preorder_nodes(mst))

        return list(order)


class KruskalMSTReorderer(MSTReorderer):
    def __init__(self, strategy: SimilarityStrategy):
        super().__init__(strategy)
        self.mst_builder = KruskalMSTBuilder()


class PrimMSTReorderer(MSTReorderer):
    def __init__(self, strategy: SimilarityStrategy):
        super().__init__(strategy)
        self.mst_builder = PrimMSTBuilder()


class Available(CommandModuleMap):
    NAIVE = KeyVal("naive", NaiveReorderer)
    GREEDY = KeyVal("greedy", GreedyReorderer)
    KRUSKAL = KeyVal("kruskal", KruskalMSTReorderer)
    PRIM = KeyVal("prim", PrimMSTReorderer)


def apply_from(*, method: str | None = None) -> type[MSTReorderer]:
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


class SimilarCommand(Command):
    command_id: str = "similar"

    def __init__(self, reorderer: ReordererStrategy, *, reverse=False):
        self.reorderer = reorderer
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        sorted_words_seq = self.reorderer.find_optimal_order(prompt)
        return (
            sorted_words_seq if not self.reverse else list(reversed(sorted_words_seq))
        )

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
    def get_reorderer(cmd: "commands.Commands") -> ReordererStrategy:
        """Instanciate one reorder function from the parsed result."""

        def get_class(cmd: "commands.Commands"):
            query = cmd.similar_method
            if query != "mst":
                return apply_from(method=query)

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

        return cls(strategy=SequenceMatcherSimilarity())

    @classmethod
    def create_from_cmd(
        cls, cmd: "commands.Commands", *, reverse=False
    ) -> "SimilarCommand":
        """Alternative method."""
        return cls(reorderer=cls.get_reorderer(cmd), reverse=reverse)
