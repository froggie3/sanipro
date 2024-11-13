import itertools
import logging
import typing


class BufferingLoggerWriter(typing.IO):
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


def batched(iterable: typing.Iterable, n: int, *, strict: bool = False):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError("batched(): incomplete batch")
        yield batch


def capped(iterable, n: int) -> typing.Generator[int, None, None]:
    return (x % n for x in iterable)


def cmp_helper(
    a: typing.Any,
    b: typing.Any,
    key: typing.Callable | None = None,
    reverse: bool = False,
):
    if key is not None:
        return key(b) <= key(a) if reverse else key(a) <= key(b)

    return b <= a if reverse else a <= b


def get_log_level_from(count: int | None) -> int:
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


def to_dict(obj):
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")}


class HasPrettyRepr:
    def __repr__(self):
        params = ", ".join(f"{k}={v!r}" for k, v in to_dict(self).items())
        return f"{self.__class__.__name__}({params})"


debug_fp = BufferingLoggerWriter(logging.getLogger(__name__), logging.DEBUG)
