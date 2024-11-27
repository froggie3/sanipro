import atexit
import logging
import os
import readline
import typing

from . import color


def logger_add_handler() -> None:
    logging.basicConfig(
        format=(
            f"{color.default}[%(levelname)s]{color.RESET} "
            f"{color.default}%(module)s/%(funcName)s{color.RESET} "
            f"{color.default}(%(lineno)d):{color.RESET} "
            f"%(message)s"
        ),
        datefmt=r"%Y-%m-%d %H:%M:%S",
    )


def prepare_readline() -> None:
    histfile = os.path.join(os.path.expanduser("~"), ".sanipro_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, histfile)


def execute(hooks: tuple[typing.Callable, ...]) -> None:
    for fun in hooks:
        fun()


init = (logger_add_handler,)

interactive = (prepare_readline,)


if __name__ != "__main__":
    pass
