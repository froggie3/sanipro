from abc import ABC, abstractmethod

import networkx

from sanipro.abc import MutablePrompt, Prompt


class ExecutePrompt(ABC):
    @abstractmethod
    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        """Processes the prompt from the input, and returns another mutable prompt."""


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


class MSTBuilder(ABC):
    """MSTを構築する戦略のインターフェース"""

    @abstractmethod
    def build_mst(self, graph: networkx.Graph) -> networkx.Graph:
        pass
