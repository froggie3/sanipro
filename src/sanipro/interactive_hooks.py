import atexit
import logging
import os
import readline
import sys
import time


def logger_add_handler():
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))


def show_welcome_message():
    prog = "Sanipro"
    version = ".".join(("0", "1"))
    dt = time.asctime()
    welcome_message = (
        f"{prog} (created by iigau) in interactive mode\n"
        f"Program was launched up at {dt}."
    )

    print(welcome_message)


def prepare_readline():
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, histfile)


if __name__ != "__main__":
    hooks = (
        logger_add_handler,
        prepare_readline,
        show_welcome_message,
    )

    for fun in hooks:
        fun()
