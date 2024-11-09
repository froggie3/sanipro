import atexit
import logging
import os
import readline
import sys
import time
import typing

from . import color


class Logformatter(logging.Formatter):
    default_time_format = "%Y-%m-%d %H:%M:%S"
    default_msec_format = "%s.%03d"


def logger_add_handler() -> None:
    logger = logging.getLogger(__name__)

    handler = logging.StreamHandler(sys.stdout)

    fmt = (
        f"{color.default}[%(levelname)s]{color.RESET} "
        f"{color.default}%(module)s/%(funcName)s{color.RESET} "
        f"{color.default}(%(lineno)d):{color.RESET} "
        f"%(message)s"
    )

    formatter = Logformatter(fmt=fmt)

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def show_welcome_message() -> None:
    prog = "Sanipro"
    version = ".".join(("0", "1"))
    dt = time.asctime()
    welcome_message = (
        f"{prog} (created by iigau) in interactive mode\n"
        f"Program was launched up at {dt}."
    )

    print(welcome_message)


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


init = (
    logger_add_handler,
    show_welcome_message,
)

interactive = (prepare_readline,)


if __name__ != "__main__":
    pass
