import argparse
import logging
import sys
from pprint import pprint

from . import cli_hooks, color
from .abc import TokenInterface
from .common import Delimiter, FuncConfig, PromptBuilder
from .filters import exclude, mask, random, sort, sort_all, unique
from .parser import ParserV1, ParserV2, TokenInteractive, TokenNonInteractive

logger = logging.getLogger()


class Subcommand:
    """the name definition for the subcommands"""

    MASK = "mask"
    RANDOM = "random"
    SORT = "sort"
    SORT_ALL = "sort-all"
    UNIQUE = "unique"


class Commands:
    # features usable in parser_v1
    mask = False
    random = False
    sort = False
    sort_all = "lexicographical"
    unique = False

    # basic functions
    exclude = False
    input_delimiter = ","
    interactive = False
    output_delimiter = ", "
    ps1 = f"{color.default}>>>{color.RESET} "
    replace_to = r"%%%"
    subcommand = ""
    use_parser_v2 = False
    verbose = False

    # subcommands options
    reverse = False

    def get_logger_level(self) -> int:
        return logging.DEBUG if self.verbose else logging.INFO

    def debug(self) -> None:
        logger.debug(f"CLI parameters={self!r}")

    @classmethod
    def prepare_parser(cls) -> argparse.ArgumentParser:
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
            default=cls.input_delimiter,
            help="specifies the delimiter for the original prompts",
        )
        parser.add_argument(
            "--output-delimiter",
            default=cls.output_delimiter,
            help="specifies the delimiter for the processed prompts",
        )
        parser.add_argument(
            "--ps1",
            default=cls.ps1,
            help="specifies the custom format for the prompts",
        )
        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="enables interactive input eternally",
        )
        parser.add_argument(
            "-e", "--exclude", nargs="*", help="exclude words specified"
        )
        parser.add_argument(
            "--use_parser_v2",
            "-2",
            action="store_true",
            help="use parse_v2 instead of the default parse_v1",
        )

        subparsers = parser.add_subparsers(dest="subcommand")

        parser_mask = subparsers.add_parser(Subcommand.MASK)
        parser_mask.add_argument(
            "mask", nargs="*", help="mask words specified rather than removing them"
        )
        parser_mask.add_argument(
            "--replace-to",
            default=cls.replace_to,
            help="in combination with --mask, specifies the new string replaced to",
        )

        parser_random = subparsers.add_parser(Subcommand.RANDOM)
        parser_random.add_argument(
            "random",
            action="store_true",
            help="BE RANDOM!",
        )

        parser_sort = subparsers.add_parser(Subcommand.SORT)
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

        parser_sort_all = subparsers.add_parser(Subcommand.SORT_ALL)
        parser_sort_all.add_argument(
            "sort-all",
            metavar="sort_law_name",
            default=cls.sort_all,
            const=cls.sort_all,
            nargs="?",
            choices=("lexicographical", "length", "strength"),
            help="reorder all the prompt (default: %(default)s)",
        )
        parser_sort_all.add_argument(
            "--reverse",
            action="store_true",
            help="the same as above but with reversed order",
        )

        parser_unique = subparsers.add_parser(Subcommand.UNIQUE)
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

        return parser

    @classmethod
    def from_sys_argv(cls, argv: list) -> "Commands":
        parser = cls.prepare_parser()
        args = parser.parse_args(argv, namespace=cls())

        return args


class Runner:
    def __init__(self, builder: PromptBuilder, ps1: str, prpt: type[TokenInterface]):
        self.builder = builder
        self.ps1 = ps1
        self.prpt = prpt

    def run_once(
        self,
    ) -> None:
        sentence = input(self.ps1).strip()
        if sentence != "":
            self.builder.parse(sentence, self.prpt, auto_apply=True)
            result = str(self.builder)
            print(result)

    def run(self):
        raise NotImplementedError

    @staticmethod
    def from_args(
        builder: PromptBuilder, ps1: str, is_interactive: bool = False
    ) -> "Runner":
        if is_interactive:
            return RunnerInteractive(builder, ps1=ps1, prpt=TokenInteractive)
        else:
            return RunnerNonInteractive(builder, ps1="", prpt=TokenNonInteractive)


class RunnerInteractive(Runner):
    def run(self):
        cli_hooks.execute(cli_hooks.interactive)
        while True:
            try:
                self.run_once()
            except ValueError as e:
                logger.exception(f"error: {e}")
            except (IndexError, KeyError, AttributeError) as e:
                logger.exception(f"error: {e}")


class RunnerNonInteractive(Runner):
    def run(self):
        self.run_once()


def run(args: Commands) -> Runner:
    ps1 = args.ps1
    cfg = FuncConfig

    cli_hooks.execute(cli_hooks.init)

    if args.use_parser_v2 and hasattr(Subcommand, args.subcommand):
        raise NotImplementedError(
            f"the '{args.subcommand}' command is not available when using parse_v2."
        )

    builder = None
    if args.use_parser_v2:
        builder = PromptBuilder(psr=ParserV2)
    else:
        builder = Delimiter.create_builder(
            args.input_delimiter, args.output_delimiter, ParserV1
        )

    if args.use_parser_v2:
        logger.warning("using parser_v2.")
    else:

        def add_last_comma(sentence: str) -> str:
            delim = ""
            if builder.delimiter is not None:
                delim = builder.delimiter.sep_input
            if not sentence.endswith(delim):
                sentence += delim
            return sentence

        builder.append_pre_hook(add_last_comma)

    if args.subcommand == Subcommand.RANDOM:
        builder.append_hook(cfg(func=random, kwargs=()))

    if args.subcommand == Subcommand.SORT_ALL:
        from . import sort_all_factory

        sorted_partial = sort_all_factory.apply_from(args.sort_all)
        builder.append_hook(
            cfg(
                func=sort_all,
                kwargs=(
                    ("sorted_partial", sorted_partial),
                    ("reverse", True if (args.reverse or False) else False),
                ),
            )
        )

    if args.subcommand == Subcommand.SORT:
        builder.append_hook(
            cfg(func=sort, kwargs=(("reverse", (args.reverse or False)),))
        )

    if args.subcommand == Subcommand.UNIQUE:
        builder.append_hook(
            cfg(func=unique, kwargs=(("reverse", (args.reverse or False)),))
        )

    if args.subcommand == Subcommand.MASK:
        builder.append_hook(
            cfg(
                func=mask,
                kwargs=(("excludes", args.mask), ("replace_to", args.replace_to)),
            )
        )

    if args.exclude:
        builder.append_hook(cfg(func=exclude, kwargs=(("excludes", args.exclude),)))

    return Runner.from_args(builder, ps1, args.interactive)


def app():
    args = Commands.from_sys_argv(sys.argv[1:])
    logger.level = args.get_logger_level()
    args.debug()
    runner = run(args)

    try:
        runner.run()
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
