#!/usr/bin/env python3

import argparse
import atexit
import logging
import os
import readline
import sys

from lib.common import (PromptInteractive, PromptInterface,
                        PromptNonInteractive, Sentence)
from lib.parser_v2 import parse


def run_once(rs: str, ps: str, prpt: type[PromptInterface]) -> None:
    sentence = Sentence(input(ps))
    tokens = parse(sentence, prpt)
    lines = []
    for x in tokens:
        lines.append(str(x))
    print(rs.join(lines))


def run(args, rs=", ", ps=">>> ") -> None:
    if args.interactive:
        while True:
            run_once(rs, ps, PromptInteractive)
    else:
        rs = "\n"
        ps = ""
        run_once(rs, ps, PromptNonInteractive)


def main():
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")

    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)

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

    try:
        run(args)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
