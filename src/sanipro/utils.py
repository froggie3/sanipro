import logging

from sanipro.abc import TokenInterface

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
