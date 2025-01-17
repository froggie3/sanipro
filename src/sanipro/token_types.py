from enum import Enum


class SupportedInTokenType(Enum):
    """Supported token types."""

    # used in option
    A1111 = "a1111compat"
    CSV = "csv"

    @staticmethod
    def choises() -> list[str]:
        return [item.value for item in SupportedInTokenType]


class SupportedOutTokenType(Enum):
    """Supported token types."""

    # used in option
    A1111 = "a1111"
    A1111_compat = "a1111compat"
    CSV = "csv"

    @staticmethod
    def choises() -> list[str]:
        return [item.value for item in SupportedOutTokenType]
