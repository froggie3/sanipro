from abc import ABC, abstractmethod


class Tokens:
    PARENSIS_LEFT = "("
    PARENSIS_RIGHT = ")"
    COLON = ":"
    COMMA = ","
    SPACE = " "


class PromptInterface(ABC):
    @abstractmethod
    def __init__(self, name: list = [], strength: list = []) -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @name.setter
    @abstractmethod
    def name(self, x: str) -> None:
        pass

    @property
    @abstractmethod
    def strength(self) -> str:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @strength.setter
    @abstractmethod
    def strength(self, x: str) -> None:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class Prompt(PromptInterface):
    def __init__(self, name: list, strength: list) -> None:
        self._name = name
        self._strength = strength
        self._delimiter = None

    @property
    def name(self):
        return "".join(self._name).strip()

    @name.setter
    def name(self, x):
        self._name = x

    @property
    def strength(self):
        result = "".join(self._strength) if self._strength else "1.0"
        return result

    @strength.setter
    def strength(self, x):
        self._strength = x

    @property
    def length(self):
        return len(self.name)

    def __repr__(self):
        return f"{__class__.__name__}(name='{self.name}', strength={self.strength})"


class PromptInteractive(Prompt):
    def __init__(self, name: list, strength: list):
        Prompt.__init__(self, name, strength)
        self._delimiter = ":"

    def __str__(self):
        if self.strength != "1.0":
            return "({}{}{})".format(self.name, self._delimiter, self.strength)
        return self.name


class PromptNonInteractive(Prompt):
    def __init__(self, name: list, strength: list):
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
