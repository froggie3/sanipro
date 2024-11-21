import argparse
import logging
from abc import ABC, abstractmethod

from sanipro.abc import MutablePrompt, Prompt

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    def execute(self, prompt: Prompt) -> MutablePrompt: ...

    @staticmethod
    @abstractmethod
    def inject_subparser(subparser: argparse._SubParsersAction): ...


class SimilarityStrategy(ABC):
    """類似度計算の戦略インターフェース"""

    @abstractmethod
    def calculate_similarity(self, word1: str, word2: str) -> float:
        """2つの文字列の類似度を計算する"""


class ReordererStrategy(ABC):
    """並べ替えの戦略インターフェース"""

    @abstractmethod
    def __init__(self, strategy: SimilarityStrategy):
        pass

    @abstractmethod
    def find_optimal_order(self, words: Prompt) -> MutablePrompt:
        """2つの文字列の類似度を計算する"""


Edge = tuple[int, int]

WeightedEdge = tuple[float, Edge]
WeightedVertice = tuple[float, int]

AdjacencyList = list[list[int]]
AdjacencyListWeighted = list[list[WeightedVertice]]


class MSTBuilder(ABC):
    """MSTを構築する戦略のインターフェース"""

    @abstractmethod
    def build_mst(self, n: int, edges: list[WeightedEdge]) -> AdjacencyList:
        pass
