import argparse
import logging
import sys
from pprint import pprint

from .abc import TokenInterface
from .common import Delimiter, FuncConfig, PromptBuilder
from .filters import exclude, mask, random, sort, sort_all, unique
from .parser import TokenInteractive, TokenNonInteractive

logger = logging.getLogger()


def run_once(
    builder: PromptBuilder,
    ps1: str,
    prpt: type[TokenInterface],
) -> None:
    sentence = input(ps1).strip()
    if sentence != "":
        builder.parse(sentence, prpt, auto_apply=True)
        result = str(builder)
        print(result)


def run(args) -> None:
    builder = Delimiter.create_builder(args.input_delimiter, args.output_delimiter)

    delimiter = getattr(builder.delimiter, "sep_input", "")

    def add_last_comma(sentence: str) -> str:
        if not sentence.endswith(delimiter):
            sentence += delimiter
        return sentence

    builder.append_pre_hook(add_last_comma)

    ps1 = args.ps1
    cfg = FuncConfig

    # Todo: slightly redundant. may need a dedicated data structure for CLI option
    v1_commands = {
        "mask",
        "random",
        "sort",
        "sort_all",
        "unique",
    }

    if args.use_parser_v2 and args.subcommand in v1_commands:
        raise NotImplementedError(
            f"the '{args.subcommand}' command is not available when using parse_v2."
        )

    if args.use_parser_v2:
        logger.warning("using parser_v2.")

    if args.subcommand == "random":
        builder.append_hook(cfg(func=random, kwargs=()))

    if args.subcommand == "sort_all":
        from . import sort_all_factory

        sorted_partial = sort_all_factory.apply_from(args.sort_all)
        builder.append_hook(
            cfg(
                func=sort_all,
                kwargs=(
                    ("sorted_partial", sorted_partial),
                    ("reverse", True if (args.sort_all.reverse or False) else False),
                ),
            )
        )

    if args.subcommand == "sort":
        builder.append_hook(
            cfg(func=sort, kwargs=(("reverse", (args.sort.reverse or False)),))
        )

    if args.subcommand == "unique":
        builder.append_hook(
            cfg(func=unique, kwargs=(("reverse", (args.unique.reverse or False)),))
        )

    if args.subcommand == "mask":
        builder.append_hook(
            cfg(
                func=mask,
                kwargs=(("excludes", args.mask), ("replace_to", args.mask.replace_to)),
            )
        )

    if args.exclude:
        builder.append_hook(cfg(func=exclude, kwargs=(("excludes", args.exclude),)))

    if args.interactive:
        from . import interactive_hooks

        while True:
            try:
                run_once(builder, ps1, TokenInteractive)
            except ValueError as e:
                logger.exception(f"error: {e}")
    else:
        ps1 = ""
        run_once(builder, ps1, TokenNonInteractive)


def app():
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
        "--use_parser_v2",
        "-2",
        action="store_true",
        help="use parse_v2 instead of the default parse_v1",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    parser_mask = subparsers.add_parser("mask")
    parser_mask.add_argument(
        "mask", nargs="*", help="mask words specified rather than removing them"
    )
    parser_mask.add_argument(
        "--replace-to",
        default=r"%%%",
        help="in combination with --mask, specifies the new string replaced to",
    )

    parser_random = subparsers.add_parser("random")
    parser_random.add_argument(
        "random",
        action="store_true",
        help="BE RANDOM!",
    )

    parser_sort = subparsers.add_parser("sort")
    parser_sort.add_argument(
        "sort",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them consecutive",
    )
    parser_sort.add_argument(
        "--reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )

    parser_sort_all = subparsers.add_parser("sort-all")
    parser_sort_all.add_argument(
        "sort-all",
        metavar="sort_law_name",
        help="reorder all the prompt (avaliable: 'lexicographical', 'length', 'strength')",
    )
    parser_sort_all.add_argument(
        "--reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )

    parser_unique = subparsers.add_parser("unique")
    parser_unique.add_argument(
        "unique",
        action="store_true",
        help="reorder duplicate tokens with their strength to make them unique",
    )
    parser_unique.add_argument(
        "--reverse",
        action="store_true",
        help="the same as above but with reversed order",
    )

    args = parser.parse_args(sys.argv[1:])

    if args.verbose:
        logger.level = logging.DEBUG
    else:
        logger.level = logging.INFO

    logger.debug(args)
    try:
        run(args)
    except KeyboardInterrupt as e:
        print()
        sys.exit(1)
    except EOFError as e:
        print()
        sys.exit(1)
    except NotImplementedError as e:
        logger.error(f"error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"error: {e}")
        sys.exit(1)
