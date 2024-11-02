import argparse
import atexit
import logging
import os
import readline
import sys

from .abc import PromptInterface
from .common import Delimiter, FuncConfig, SentenceBuilder
from .filters import exclude, mask, random, sort, sort_all, unique
from .parser import PromptInteractive, PromptNonInteractive

logger = logging.getLogger()

logger.addHandler(logging.StreamHandler(sys.stdout))


class SortedFactory:
    available = (
        "lexicographical",
        "length",
        "strength",
    )

    @classmethod
    def sort_lexicographically(cls, prompt: PromptInterface) -> str:
        return prompt.name

    @classmethod
    def sort_by_length(cls, prompt: PromptInterface) -> int:
        return prompt.length

    @classmethod
    def sort_by_strength(cls, prompt: PromptInterface) -> str:
        return prompt.strength

    @classmethod
    def apply_from(cls, sort_law_name: str):
        import functools

        funcs = (
            cls.sort_lexicographically,
            cls.sort_by_length,
            cls.sort_by_strength,
        )
        f = None

        for func_name, func in zip(cls.available, funcs):
            if func_name.startswith(sort_law_name):
                f = functools.partial(sorted, key=func)
                break
        else:
            raise Exception(f"no matched sort law for '{sort_law_name}'")
        return f


def run_once(
    builder: SentenceBuilder,
    ps1: str,
    prpt: type[PromptInterface],
) -> None:
    sentence = input(ps1)
    tokens = builder.parse(sentence, prpt)

    builder.apply(tokens)

    result = str(builder)
    print(result)


def run(args) -> None:
    builder = Delimiter.create_builder(args.input_delimiter, args.output_delimiter)
    ps1 = args.ps1

    if args.random:
        builder.append_hook(FuncConfig(func=random, kwargs=()))
    if args.sort_all:
        builder.append_hook(
            FuncConfig(
                func=sort_all,
                kwargs=(
                    ("sorted_partial", SortedFactory.apply_from(args.sort_all)),
                    ("reverse", False),
                ),
            )
        )
    elif args.sort_all_reverse:
        builder.append_hook(
            FuncConfig(
                func=sort_all,
                kwargs=(
                    ("sorted_partial", SortedFactory.apply_from(args.sort_all)),
                    ("reverse", True),
                ),
            )
        )
    if args.sort:
        builder.append_hook(FuncConfig(func=sort, kwargs=(("reverse", False),)))
    elif args.sort_reverse:
        builder.append_hook(FuncConfig(func=sort, kwargs=(("reverse", True),)))
    if args.unique:
        builder.append_hook(FuncConfig(func=unique, kwargs=(("reverse", False),)))
    elif args.unique_reverse:
        builder.append_hook(FuncConfig(func=unique, kwargs=(("reverse", True),)))
    if args.exclude:
        builder.append_hook(
            FuncConfig(func=exclude, kwargs=(("excludes", args.exclude),))
        )
    if args.mask:
        builder.append_hook(
            FuncConfig(
                func=mask,
                kwargs=(
                    ("excludes", args.mask),
                    ("replace_to", args.mask_replace_to),
                ),
            )
        )

    if args.interactive:
        while True:
            run_once(builder, ps1, PromptInteractive)
    else:
        ps1 = ""
        run_once(builder, ps1, PromptNonInteractive)


def app():
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")

    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

    atexit.register(readline.write_history_file, histfile)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="displays extra amount of logs for debugging",
    )
    parser.add_argument(
        "-d",
        "--input-delimiter",
        default=",",
        help="specifies the delimiter for the original prompts",
    )
    parser.add_argument(
        "--output-delimiter",
        default=", ",
        help="specifies the delimiter for the processed prompts",
    )
    parser.add_argument(
        "--ps1",
        default=">>> ",
        help="specifies the custom format for the prompts",
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
    parser.add_argument(
        "--mask-replace-to",
        default=r"%%%",
        help="in combination with --mask, specifies the new string replaced to",
    )

    group_sort = parser.add_mutually_exclusive_group()
    group_sort.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="BE RANDOM!",
    )
    group_sort.add_argument(
        "--sort-all",
        metavar="sort_law_name",
        help="reorder all the prompt (avaliable: 'lexicographical', 'length', 'strength')",
    )
    group_sort.add_argument(
        "--sort-all-reverse",
        metavar="sort_law_name",
        help="the same as above but with reversed order",
    )
    group_sort.add_argument(
        "-s",
        "--sort",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them consecutive",
    )
    group_sort.add_argument(
        "--sort-reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )
    group_sort.add_argument(
        "-u",
        "--unique",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them unique",
    )
    group_sort.add_argument(
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
    except (KeyboardInterrupt, EOFError) as e:
        print()
        sys.exit(1)
    except Exception as e:
        logger.exception(f"error: {e}")
        sys.exit(1)
