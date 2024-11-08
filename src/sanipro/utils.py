import itertools
import logging
import pprint
import typing

logger = logging.getLogger()


class BufferingLoggerWriter(typing.IO):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message):
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

    def flush(self):
        pass

    def close(self):
        pass


debug_fp = BufferingLoggerWriter(logger, logging.DEBUG)


def batched(iterable, n, *, strict=False):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError("batched(): incomplete batch")
        yield batch


def capped(iterable, n):
    return (x % n for x in iterable)


def cmp_helper(a, b, key=None, reverse=False):
    if key is not None:
        return key(b) <= key(a) if reverse else key(a) <= key(b)

    return b <= a if reverse else a <= b


from random import randrange


def sorted(collection: list, *, key=None, reverse=False) -> list:
    # Base case: if the collection has 0 or 1 elements, it is already sorted
    if len(collection) < 2:
        return collection

    # Randomly select a pivot index and remove the pivot element from the collection
    pivot_index = randrange(len(collection))
    pivot = collection.pop(pivot_index)

    # Partition the remaining elements into two groups: lesser or equal, and greater
    lesser = [item for item in collection if cmp_helper(item, pivot, key=key)]
    greater = [
        item for item in collection if cmp_helper(item, pivot, key=key, reverse=True)
    ]

    # Recursively sort the lesser and greater groups, and combine with the pivot
    return [
        *sorted(lesser, key=key, reverse=reverse),
        pivot,
        *sorted(greater, key=key, reverse=reverse),
    ]
