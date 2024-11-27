from abc import ABC, abstractmethod
import argparse


class Command(ABC):
    @classmethod
    @abstractmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction): ...
