import itertools
import random
from difflib import SequenceMatcher

import networkx as nx
from networkx import traversal
from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.filters.abc import (
    ExecutePrompt,
    MSTBuilder,
    ReordererStrategy,
    SimilarityStrategy,
)

try:
    import Levenshtein  # type: ignore

    class LevenshteinSimilarity(SimilarityStrategy):
        """Similarity calculation using Levenshtein distance."""

        def calculate_similarity(self, word1: str, word2: str) -> float:
            distance = Levenshtein.distance(word1, word2)
            max_len = max(len(word1), len(word2))
            return 1 - (distance / max_len)

except ImportError:
    pass


class SequenceMatcherSimilarity(SimilarityStrategy):
    """Similarity calculation using Python built-in SequenceMatcher"""

    def calculate_similarity(self, word1: str, word2: str) -> float:
        return SequenceMatcher(None, word1, word2).ratio()


class NaiveReorderer(ReordererStrategy):
    """Tries all permutations of a token array,
    and sorts it by similarity."""

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        best_order: tuple[TokenInterface, ...] = tuple()
        best_score = float("-inf")

        # try all permutations to find the order with the highest score
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
    """Attempt a greedy sort."""

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
        # shuffle and choose random initial elements
        words = list(words[:])
        random.shuffle(words)
        result = [words.pop()]
        visited = [False] * len(words)

        # choose the most similar words
        while True:
            last_word = result[-1].name
            next_idx = self._find_max_idx(last_word, words, visited)

            # if you can't find it after searching, you've already searched everything.
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
    """Minimum spanning tree sorting strategy"""

    mst_builder: MSTBuilder

    def __init__(self, strategy: SimilarityStrategy):
        self.strategy = strategy

    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        # construct an edge list for a complete graph
        graph = nx.Graph()

        for (u, _p), (v, _q) in itertools.combinations(enumerate(words), 2):
            similarity = self.strategy.calculate_similarity(_p.name, _q.name)
            # The higher the similarity, the lower the weight
            graph.add_edge(u, v, weight=1 - similarity)

        # construct a mst
        mst = self.mst_builder.build_mst(graph)

        # search the minimum spanning tree using DFS and determine the order
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


class SimilarCommand(ExecutePrompt):
    def __init__(self, reorderer: ReordererStrategy, *, reverse=False):
        self.reorderer = reorderer
        self.reverse = reverse

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        sorted_words_seq = self.reorderer.find_optimal_order(prompt)
        return (
            sorted_words_seq if not self.reverse else list(reversed(sorted_words_seq))
        )
