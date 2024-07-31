class Tokens:
    PARENSIS_LEFT = "("
    PARENSIS_RIGHT = ")"
    COLON = ":"
    COMMA = ","
    SPACE = " "


class Prompt:
    def __init__(self, name=None, strength=None) -> None:
        if name is None:
            name = []
        if strength is None:
            strength = []
        self._name = name
        self._strength = strength

    @property
    def name(self) -> str:
        return "".join(self._name).strip()

    @property
    def strength(self) -> str:
        result = "".join(self._strength) if self._strength else "1.0"
        # return float()
        return result

    @property
    def length(self) -> int:
        return len(self.name)

    def __repr__(self) -> str:
        return f"{__class__.__name__}(name='{self.name}', strength={self.strength})"


class PromptInteractive(Prompt):
    def __init__(self, name=None, strength=None):
        Prompt.__init__(self, name, strength)
        self._delimiter = ":"

    def __str__(self) -> str:
        if self.strength != "1.0":
            return f"({self.name}{self._delimiter}{self.strength})"
        return self.name


class PromptNonInteractive(Prompt):
    def __init__(self, name=None, strength=None):
        Prompt.__init__(self, name, strength)
        self._delimiter = "\t"

    def __str__(self) -> str:
        if self.strength != "1.0":
            return f"{self.name}{self._delimiter}{self.strength}"
        return self.name


class PromptList(list):
    def __str__(self) -> str:
        result = "\n".join([str(token) for token in self])
        return result


class Sentence:
    def __init__(self, sentence: str) -> None:
        self.index = 0
        # 簡単のために最後が ', ' で終わるようにする
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
    """char から stack に一文字追加"""
    stack.append(char)


PromptClass = type[PromptInteractive | PromptNonInteractive]
