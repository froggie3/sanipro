import logging
import time
import typing

from . import utils

logger = logging.getLogger(__name__)


class LinearCongruentialGenerator:
    """Notorious rand() simulation"""

    def __init__(
        self,
        *,
        multiplier=1103515245,
        increment=12345,
        modulo=1 << 31,
        seed=int(time.time() * 100),
        shift=16
    ):
        self.multiplier = multiplier
        self.increment = increment
        self.seed = seed
        self.modulo = modulo
        self.bit_lshift = shift

    def _next_number(self) -> typing.Generator[int, None, None]:
        while True:
            self.seed = (self.multiplier * self.seed + self.increment) % self.modulo
            yield self.seed

    def random(self) -> typing.Generator[int, None, None]:
        while True:
            self.seed = next(self._next_number())
            buffer = self.seed >> self.bit_lshift
            yield buffer

    @classmethod
    def shuffle(cls, iterable):
        lcg = cls()

        solved_num = 0
        length = len(iterable)
        iterator = utils.capped(lcg.random(), length)

        for one, two in utils.batched(iterator, 2):
            if solved_num < length:
                iterable[one], iterable[two] = iterable[two], iterable[one]
                solved_num += 1
            else:
                break

        return iterable

    @classmethod
    def shuffled(cls, iterable):
        lcg = cls()

        solved_num = 0
        length = len(iterable)
        check_arr = [True] * length
        iterator = utils.capped(lcg.random(), length)

        new_list = []

        for idx in iterator:
            if solved_num < length:
                if check_arr[idx]:
                    check_arr[idx] = False
                    new_list.append(iterable[idx])
                    solved_num += 1
            else:
                break

        return new_list
