import logging
from abc import ABC, abstractmethod

logger = logging.getLogger()


class TokenInterface(ABC):
    @abstractmethod
    def __init__(self, name: str, strength: str) -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def strength(self) -> str:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def replace(self, replace: str) -> "TokenInterface":
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass
