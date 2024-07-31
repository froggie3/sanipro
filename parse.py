#!/usr/bin/env python3

import os
import sys
import atexit
import logging
import readline

import lib.common
import lib.parser_v2

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))

if "-v" in sys.argv:
    logger.level = logging.DEBUG
else:
    logger.level = logging.INFO


def main():
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)

    if "-i" in sys.argv:
        while True:
            try:
                sentence = lib.parser_v2.Sentence(input(">>> "))
            except (KeyboardInterrupt, EOFError):
                print()
                return

            tokens = lib.parser_v2.parse(
                sentence,
                lib.common.PromptInteractive
            )
            # tokens.sort(key=lambda x: x.strength)
            logger.info(f"{tokens}".format(tokens))
    else:
        try:
            sentence = lib.parser_v2.Sentence(input())
        except (KeyboardInterrupt, EOFError):
            print()
            return

        tokens = lib.parser_v2.parse(
            sentence,
            lib.common.PromptNonInteractive
        )
        logger.info(f"{tokens}".format(tokens))


if __name__ == '__main__':
    main()
