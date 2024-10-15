import argparse
import atexit
import logging
import os
import readline
import sys

from .common import PromptInteractive, PromptInterface, PromptNonInteractive, Sentence
from .parser_v2 import FuncConfig, apply, exclude, mask, parse, sort, unique


def run_once(args, rs: str, ps: str, prpt: type[PromptInterface]) -> None:
    sentence = Sentence(input(ps))
    tokens = parse(sentence, prpt)

    func_config: list[FuncConfig] = []
    if args.sort:
        func_config.append({"func": sort, "kwargs": {"reverse": False}})
    elif args.sort_reverse:
        func_config.append({"func": sort, "kwargs": {"reverse": True}})
    if args.unique:
        func_config.append({"func": unique, "kwargs": {"reverse": False}})
    if args.unique_reverse:
        func_config.append({"func": unique, "kwargs": {"reverse": True}})
    if args.exclude:
        func_config.append({"func": exclude, "kwargs": {"excludes": args.exclude}})
    if args.mask:
        func_config.append({"func": mask, "kwargs": {"excludes": args.mask}})

    tokens = apply(tokens, func_config)

    lines = []
    for x in tokens:
        lines.append(str(x))
    print(rs.join(lines))


def run(args, rs=", ", ps=">>> ") -> None:
    if args.interactive:
        while True:
            run_once(args, rs, ps, PromptInteractive)
    else:
        rs = "\n"
        ps = ""
        run_once(args, rs, ps, PromptNonInteractive)


def app():
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="displays extra amount of logs for debugging",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="enables interactive input eternally",
    )
    parser.add_argument("-e", "--exclude", nargs="*", help="exclude words specified")
    parser.add_argument(
        "-m", "--mask", nargs="*", help="mask words specified rather than removing them"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--sort",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them consecutive",
    )
    group.add_argument(
        "--sort-reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )
    group.add_argument(
        "-u",
        "--unique",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them unique",
    )
    group.add_argument(
        "--unique-reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.level = logging.DEBUG
    else:
        logger.level = logging.INFO

    logger.debug(args)
    try:
        run(args)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)
