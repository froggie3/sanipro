import argparse
import heapq
import itertools
import logging
import random
from difflib import SequenceMatcher

from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.commandline import commands
from sanipro.commandline.help_formatter import SaniproHelpFormatter
from sanipro.utils import CommandModuleMap, KeyVal, ModuleMatcher

from .abc import (AdjacencyList, Command, MSTBuilder, ReordererStrategy,
                  SimilarityStrategy, WeightedEdge)
from .filter import Filter

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
    def build_mst(self, n: int, edges: list[WeightedEdge]) -> AdjacencyList:
        # エッジリストを隣接リストに変換
        graph = [[] for _ in range(n)]
        for weight, (u, v) in edges:
            graph[u].append((weight, v))
            graph[v].append((weight, u))

        # 最小全域木のエッジを格納するリスト
        mst_edges: list[tuple[int, int]] = []
        visited = set()
        min_heap = []

        # 開始ノードを0とする
        start_node = 0
        visited.add(start_node)

        # 開始ノードから到達可能なエッジをヒープに追加
        for weight, neighbor in graph[start_node]:
            heapq.heappush(min_heap, (weight, start_node, neighbor))

        # Prim法のメインループ
        while min_heap and len(visited) < n:
            weight, u, v = heapq.heappop(min_heap)
            if v in visited:
                continue
            mst_edges.append((u, v))
            visited.add(v)
            for next_weight, next_node in graph[v]:
                if next_node not in visited:
                    heapq.heappush(min_heap, (next_weight, v, next_node))

        # グラフの構築（無向グラフ）
        mst = [[] for _ in range(n)]
        for u, v in mst_edges:
            mst[u].append(v)
            mst[v].append(u)

        return mst


class UnionFind:
    """Union-Find構造のヘルパークラス"""

    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, node):
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u != root_v:
            if self.rank[root_u] > self.rank[root_v]:
                self.parent[root_v] = root_u
            elif self.rank[root_u] < self.rank[root_v]:
                self.parent[root_u] = root_v
            else:
                self.parent[root_v] = root_u
                self.rank[root_u] += 1


class KruskalMSTBuilder(MSTBuilder):
    def build_mst(self, n: int, edges: list[WeightedEdge]) -> AdjacencyList:
        # 重みの昇順にエッジをソート
        edges.sort()
        uf = UnionFind(n)
        mst_edges = []

        for weight, (u, v) in edges:
            if uf.find(u) != uf.find(v):
                uf.union(u, v)
                mst_edges.append((u, v))
                if len(mst_edges) == n - 1:
                    break

        # グラフの構築（無向グラフ）
        mst = [[] for _ in range(n)]
        for u, v in mst_edges:
            mst[u].append(v)
            mst[v].append(u)

        return mst


class MSTReorderer(ReordererStrategy):
    """最小全域木による並べ替え戦略"""

    mst_builder: MSTBuilder

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        words = list(words[:])
        n = len(words)

        # 完全グラフのエッジリストを構築
        edges: list[WeightedEdge] = []
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.strategy.calculate_similarity(
                    words[i].name, words[j].name
                )
                weight = 1 - similarity  # 類似度が高いほど重みは低くする
                edges.append((weight, (i, j)))

        # MSTを構築
        mst = self.mst_builder.build_mst(n, edges)

        # 最小全域木をDFSで探索し、順序を決定
        visited = [False] * n
        order = []

        def dfs(node):
            visited[node] = True
            order.append(words[node])
            for neighbor in mst[node]:
                if not visited[neighbor]:
                    dfs(neighbor)

        dfs(0)  # 0番目の頂点から探索開始
        return order


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
    def __init__(self, reorderer: ReordererStrategy, *, reverse=False):
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
    def get_instance(cmd: "commands.Commands") -> ReordererStrategy:
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
