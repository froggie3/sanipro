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
        if self._delimiter is None:
            raise NotImplementedError

        if self.strength != "1.0":
            return f"({self.name}{self._delimiter}{self.strength})"
        return self.name


class PromptInteractive(Prompt):
    def __init__(self, name=[], strength=[]):
        Prompt.__init__(self, name, strength)
        self._delimiter = ":"


class PromptNonInteractive(Prompt):
    def __init__(self, name=[], strength=[]):
        Prompt.__init__(self, name, strength)
        self._delimiter = "\t"


class PromptList(list):
    def __str__(self) -> str:
        result = "\n".join([str(token) for token in self])
        return result


class Sentence:
    def __init__(self, sentence: str) -> None:
        self.index = 0
        # for simplicity of implementation, end sentence with a comma
        added_char = Tokens.COMMA if sentence[-1] != Tokens.COMMA else ""
        self.sentence = sentence + added_char

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.sentence):
            result = self.sentence[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration


def read_char(stack, char) -> None:
    stack.append(char)


PromptClass = type[PromptInteractive | PromptNonInteractive]
