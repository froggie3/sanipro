#!/usr/bin/env python3

import os
import atexit
import logging
import readline

import lib.parser_v2

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
# logger.level = logging.INFO
logger.level = logging.DEBUG


def main():
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)

    while True:
        sentence = lib.parser_v2.Sentence(
            input(">>> ")
        )
        tokens = lib.parser_v2.parse(sentence)
        # tokens.sort(key=lambda x: x.strength)
        logger.info(f"{tokens}".format(tokens))


if __name__ == '__main__':
    main()
