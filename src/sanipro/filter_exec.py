import functools
from abc import ABC, abstractmethod

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt


class IFilterExecutor(ABC):
    """Filter executor interface."""

    @abstractmethod
    def execute_filter_all(self, prompts: Prompt) -> MutablePrompt:
        """Sequentially applies the filters."""

    @abstractmethod
    def append_command(self, *command: ExecutePrompt) -> None:
        """Appends filters."""

    @abstractmethod
    def remove_command(self, command: ExecutePrompt) -> None:
        """Removes a filter."""

    @abstractmethod
    def clear_commands(self) -> None:
        """Removes all filters."""

    @abstractmethod
    def get_commands(self) -> list[ExecutePrompt]:
        """Returns all filters."""


class FilterExecutor(IFilterExecutor):
    _funcs: list[ExecutePrompt]

    def __init__(self) -> None:
        self._funcs = []
        self._tokens: MutablePrompt = []

    def execute_filter_all(self, prompts: Prompt) -> MutablePrompt:
        result = functools.reduce(
            lambda x, y: y.execute_prompt(x), self._funcs, prompts
        )
        self._tokens = list(result)
        return self._tokens

    def append_command(self, *command: ExecutePrompt) -> None:
        self._funcs.extend(command)

    def remove_command(self, command: ExecutePrompt) -> None:
        self._funcs.remove(command)

    def clear_commands(self) -> None:
        self._funcs.clear()

    def get_commands(self) -> list[ExecutePrompt]:
        return self._funcs

    @property
    def tokens(self) -> MutablePrompt:
        return self._tokens
