from abc import ABC, abstractmethod


class Tokens:
    PARENSIS_LEFT = "("
    PARENSIS_RIGHT = ")"
    COLON = ":"
    COMMA = ","
    SPACE = " "


class PromptInterface(ABC):
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
    def replace(self, replace: str) -> "PromptInterface":
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class Prompt(PromptInterface):
    def __init__(self, name: str, strength: str) -> None:
        self._name = name
        self._strength = strength
        self._delimiter = None

    @property
    def name(self):
        return self._name

    @property
    def strength(self):
        return self._strength

    @property
    def length(self):
        return len(self.name)

    def replace(self, replace="***"):
        return type(self)(replace, self._strength)

    def __repr__(self):
        items = (f"{k}={v!r}" for k, v in self.__dict__.items())
        return "{}({})".format(type(self).__name__, ", ".join(items))


class PromptInteractive(Prompt):
    def __init__(self, name: str, strength: str):
        Prompt.__init__(self, name, strength)
        self._delimiter = ":"

    def __str__(self):
        if self.strength != "1.0":
            return "({}{}{})".format(self.name, self._delimiter, self.strength)
        return self.name


class PromptNonInteractive(Prompt):
    def __init__(self, name: str, strength: str):
        Prompt.__init__(self, name, strength)
        self._delimiter = "\t"

    def __str__(self):
        return "{}{}{}".format(self.strength, self._delimiter, self.name)


class Sentence(str):
    def __new__(cls, sentence: str):
        # for simplicity of implementation
        if not sentence.endswith(Tokens.COMMA):
            sentence += Tokens.COMMA
        return super().__new__(cls, sentence)


def read_char(stack, char) -> None:
    stack.append(char)
