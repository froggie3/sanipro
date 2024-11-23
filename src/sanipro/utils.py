import logging
import typing
from dataclasses import dataclass

from .abc import TokenInterface

logger = logging.getLogger(__name__)


def to_dict(obj) -> dict:
    """Creates a dictionary from the object without magic methods."""
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


class HasPrettyRepr:
    """A base class that contains human readable representation of the object."""

    def __repr__(self):
        params = ", ".join(f"{k}={v!r}" for k, v in to_dict(self).items())
        return f"{self.__class__.__name__}({params})"


def round_token_weight(token: TokenInterface, digits: int) -> TokenInterface:
    """A helper function to round the token weight to `n` digits."""
    return type(token)(token.name, round(token.weight, digits))


@dataclass
class KeyVal:
    """
    Arguments:
        key: コマンド名
        val: 呼び出し可能なモジュール名
    """

    key: str
    val: typing.Any


class CommandModuleMap:
    """The name definition for the subcommands."""

    @classmethod
    def list_commands(cls) -> list:
        """利用可能なサブコマンドの表現の一覧を取得する"""
        return [val for key, val in cls.__dict__.items() if key.isupper()]


class ModuleMatcher:
    def __init__(self, mapping: type[CommandModuleMap]):
        if not issubclass(mapping, CommandModuleMap):
            raise TypeError("invalid command module map was given!")
        self.commands = {
            val.key: val.val for key, val in mapping.__dict__.items() if key.isupper()
        }

    def match(self, method: str) -> typing.Any:
        # Todo: typing.Any を利用しないいい方法はないか？
        result = self.commands.get(method)
        if result is None:
            raise KeyError
        return result


class FuncMatcher(ModuleMatcher):
    pass
