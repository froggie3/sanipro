import logging
import typing

from .abc import TokenInterface

logger = logging.getLogger(__name__)


class BufferingLoggerWriter(typing.IO):
    """Pseudo file object redirected to logger."""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message) -> int:
        if "\n" not in message:
            self.buffer += message
        else:
            parts = message.split("\n")
            if self.buffer:
                s = self.buffer + parts.pop(0)
                self.logger.log(self.level, s)
            self.buffer = parts.pop()
            for part in parts:
                self.logger.log(self.level, part)
        return 0

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


__debug_fp = BufferingLoggerWriter(logger, logging.DEBUG)


def get_log_level_from(count: int | None) -> int:
    """Map function that maps the number of options to log level."""
    import logging

    if count is None:
        return logging.INFO
    elif count == 0:
        return logging.INFO
    elif count == 1:
        return logging.INFO
    elif count == 2:
        return logging.DEBUG
    else:
        raise ValueError


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
    return type(token)(token.name, round(token.strength, digits))


def get_debug_fp() -> BufferingLoggerWriter:
    """Get `BufferingLoggerWriter` instance. Mainly for `pprint.pprint()`."""
    return __debug_fp
