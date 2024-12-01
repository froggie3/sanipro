import itertools
import logging
import random
from difflib import SequenceMatcher

import networkx as nx
from networkx import traversal
from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.filters.abc import (
    Command,
    MSTBuilder,
    ReordererStrategy,
    SimilarityStrategy
)

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
