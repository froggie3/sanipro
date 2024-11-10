import argparse
import logging
import pprint
import sys
from collections.abc import Sequence


from . import cli_hooks, color, utils, filters
from .abc import TokenInterface
from .common import Delimiter, FuncConfig, PromptBuilder
from .parser import ParserV1, ParserV2, TokenInteractive, TokenNonInteractive

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


class Subcommand:
    """the name definition for the subcommands"""

    MASK = "mask"
    RANDOM = "random"
    SORT = "sort"
    SORT_ALL = "sort-all"
    UNIQUE = "unique"


class Commands(utils.HasPrettyRepr):
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
    roundup = 2
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
        pprint.pprint(self, utils.debug_fp)

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
            "-r",
            "--roundup",
            default=cls.roundup,
            type=int,
            help="round up to x digits",
        )
        parser.add_argument(
            "-e",
            "--exclude",
            nargs="*",
            help="exclude words specified",
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
            "mask",
            nargs="*",
            help="mask words specified rather than removing them",
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

    def get_builder(self) -> PromptBuilder:
        cfg = FuncConfig

        if self.use_parser_v2 and hasattr(Subcommand, self.subcommand):
            raise NotImplementedError(
                f"the '{self.subcommand}' command is not available "
                "when using parse_v2."
            )

        builder = None
        if self.use_parser_v2:
            builder = PromptBuilder(psr=ParserV2)
        else:
            builder = Delimiter.create_builder(
                self.input_delimiter,
                self.output_delimiter,
                ParserV1,
            )

        if self.use_parser_v2:
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

        # always round
        builder.append_hook(
            cfg(
                func=filters.round_up,
                kwargs=(("digits", self.roundup),),
            ),
        )

        if self.subcommand == Subcommand.RANDOM:
            builder.append_hook(
                cfg(
                    func=filters.random,
                    kwargs=(),
                ),
            )

        if self.subcommand == Subcommand.SORT_ALL:
            from . import sort_all_factory

            sorted_partial = sort_all_factory.apply_from(self.sort_all)
            builder.append_hook(
                cfg(
                    func=filters.sort_all,
                    kwargs=(
                        ("sorted_partial", sorted_partial),
                        ("reverse", True if (self.reverse or False) else False),
                    ),
                )
            )

        if self.subcommand == Subcommand.SORT:
            builder.append_hook(
                cfg(
                    func=filters.sort,
                    kwargs=(
                        (
                            "reverse",
                            (self.reverse or False),
                        ),
                    ),
                )
            )

        if self.subcommand == Subcommand.UNIQUE:
            builder.append_hook(
                cfg(
                    func=filters.unique,
                    kwargs=(("reverse", (self.reverse or False)),),
                )
            )

        if self.subcommand == Subcommand.MASK:
            builder.append_hook(
                cfg(
                    func=filters.mask,
                    kwargs=(
                        ("excludes", self.mask),
                        ("replace_to", self.replace_to),
                    ),
                )
            )

        if self.exclude:
            builder.append_hook(
                cfg(
                    func=filters.exclude,
                    kwargs=(("excludes", self.exclude),),
                ),
            )

        return builder

    @classmethod
    def from_sys_argv(cls, arg_val: Sequence) -> "Commands":
        parser = cls.prepare_parser()
        args = parser.parse_args(arg_val, namespace=cls())

        return args


class Runner(utils.HasPrettyRepr):
    def __init__(
        self,
        builder: PromptBuilder,
        ps1: str,
        prpt: type[TokenInterface],
    ):
        self.builder = builder
        self.ps1 = ps1
        self.prpt = prpt

    def _run_once(
        self,
    ) -> None:
        sentence = input(self.ps1).strip()
        if sentence != "":
            self.builder.parse(
                sentence,
                self.prpt,
                auto_apply=True,
            )
            result = str(self.builder)
            print(result)

    def run(self):
        raise NotImplementedError

    @staticmethod
    def from_args(args: Commands) -> "Runner":
        builder = args.get_builder()
        if args.interactive:
            return RunnerInteractive(
                builder,
                ps1=args.ps1,
                prpt=TokenInteractive,
            )
        else:
            return RunnerNonInteractive(
                builder,
                ps1="",
                prpt=TokenNonInteractive,
            )


class RunnerInteractive(Runner):
    def run(self):
        cli_hooks.execute(cli_hooks.interactive)
        while True:
            try:
                self._run_once()
            except ValueError as e:
                logger.exception(f"error: {e}")
            except (IndexError, KeyError, AttributeError) as e:
                logger.exception(f"error: {e}")


class RunnerNonInteractive(Runner):
    def run(self):
        self._run_once()


def app():
    args = Commands.from_sys_argv(sys.argv[1:])
    cli_hooks.execute(cli_hooks.init)
    logger_root.setLevel(args.get_logger_level())
    args.debug()
    runner = Runner.from_args(args)

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
