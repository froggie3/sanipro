import time
import typing


class LCG:
    """Notorious rand() simulation"""

    def __init__(self, seed=0, shift=0):
        self.a = 1103515245
        self.x = seed
        self.c = 12345
        self.m = 1 << 31
        self.bit_lshift = shift

    def _random(self) -> typing.Generator[int, None, None]:
        while True:
            self.x = (self.a * self.x + self.c) % self.m
            yield self.x

    def random(self) -> typing.Generator[int, None, None]:
        while True:
            self.x = next(self._random())
            buffer = self.x >> self.bit_lshift
            yield buffer

    @classmethod
    def shuffle(cls, iterable):
        seed = int(time.time() * 100)
        lcg = cls(seed, shift=20)

        solved_num = 0
        length = len(iterable)
        check_arr = [True] * length

        new_list = []

        for idx in lcg.random():
            if solved_num < length:
                idx %= length
                if check_arr[idx]:
                    check_arr[idx] = False
                    new_list.append(iterable[idx])
                    solved_num += 1
            else:
                break

        return new_list

    @classmethod
    def shuffled(cls, iterable):
        seed = int(time.time() * 100)
        lcg = cls(seed, shift=20)

        solved_num = 0
        length = len(iterable)
        check_arr = [True] * length

        new_list = []

        for idx in lcg.random():
            if solved_num < length:
                idx %= length
                if check_arr[idx]:
                    check_arr[idx] = False
                    new_list.append(iterable[idx])
                    solved_num += 1
            else:
                break

        return new_list
