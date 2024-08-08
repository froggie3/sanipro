#!/usr/bin/env python3

import argparse
import atexit
import logging
import os
import readline
import sys

from lib.common import PromptInteractive, PromptNonInteractive, Sentence
from lib.parser_v2 import parse

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler(sys.stdout))


parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true",
                    help="displays extra amount of logs for debugging")
parser.add_argument("-i", "--interactive", action="store_true",
                    help="enables interactive input eternally")
args = parser.parse_args()

if args.verbose:
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

    if args.interactive:
        while True:
            try:
                sentence = Sentence(input(">>> "))
            except (KeyboardInterrupt, EOFError):
                print()
                sys.exit(1)

            tokens = parse(sentence, PromptInteractive)
            logger.info("{}".format(", ".join(tokens)))
    else:
        try:
            sentence = Sentence(input())
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)

        tokens = parse(sentence, PromptNonInteractive)
        logger.info("{}".format("\n".join(tokens)))


if __name__ == '__main__':
    main()
