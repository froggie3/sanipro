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
