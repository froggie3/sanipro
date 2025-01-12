from sanipro.abc import TokenInterface
from sanipro.compatible import Self


class Token(TokenInterface):
    _delimiter: str

    def __init__(self, name: str, weight: float) -> None:
        self._name = name
        self._weight = float(weight)

    @property
    def name(self) -> str:
        return self._name

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def length(self) -> int:
        return len(self.name)

    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> Self:
        if new_name is None:
            new_name = self._name
        if new_weight is None:
            new_weight = self._weight

        return type(self)(new_name, new_weight)

    def __repr__(self) -> str:
        items = (f"{v!r}" for v in (self.name, self.weight))
        return "{}({})".format(type(self).__name__, f", ".join(items))

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError
        return self._name == other._name and self._weight == other._weight

    def __hash__(self) -> int:
        return hash((self._name, self._weight))


class A1111Token(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)


class CSVToken(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)
