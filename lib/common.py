class Tokens:
    PARENSIS_LEFT = "("
    PARENSIS_RIGHT = ")"
    COLON = ":"
    COMMA = ","
    SPACE = " "


class Prompt:
    def __init__(self, name=[], strength=[]) -> None:
        self._name = name
        self._strength = strength
        self._delimiter = None

    @property
    def name(self) -> str:
        return "".join(self._name).strip()

    @property
    def strength(self) -> str:
        result = "".join(self._strength) if self._strength else "1.0"
        return result

    @property
    def length(self) -> int:
        return len(self.name)

    def __repr__(self) -> str:
        return f"{__class__.__name__}(name='{self.name}', strength={self.strength})"

    def __str__(self) -> str:
        raise NotImplementedError


class PromptInteractive(Prompt):
    def __init__(self, name=[], strength=[]):
        Prompt.__init__(self, name, strength)
        self._delimiter = ":"

    def __str__(self) -> str:
        if self.strength != "1.0":
            return "({}{}{})".format(self.name, self._delimiter, self.strength)
        return self.name


class PromptNonInteractive(Prompt):
    def __init__(self, name=[], strength=[]):
        Prompt.__init__(self, name, strength)
        self._delimiter = "\t"

    def __str__(self) -> str:
        return "{}{}{}".format(self.strength, self._delimiter, self.name)


class PromptList(list):
    pass


class Sentence(str):
    def __new__(cls, sentence: str):
        # for simplicity of implementation
        if not sentence.endswith(Tokens.COMMA):
            sentence += Tokens.COMMA
        return super().__new__(cls, sentence)


def read_char(stack, char) -> None:
    stack.append(char)


PromptClass = type[PromptInteractive | PromptNonInteractive]
