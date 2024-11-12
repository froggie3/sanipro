import argparse
import logging
import pprint
import sys
import time
from code import InteractiveConsole, InteractiveInterpreter
from collections.abc import Sequence

from sanipro import sort_all_factory

from . import cli_hooks, color, filters, utils
from .abc import TokenInterface
from .common import (
    Delimiter,
    FuncConfig,
    PromptBuilder,
    PromptBuilderV1,
    PromptBuilderV2,
)
from .parser import TokenInteractive, TokenNonInteractive

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


class Subcommand(object):
    """the name definition for the subcommands"""

    MASK = "mask"
    RANDOM = "random"
    SORT = "sort"
    SORT_ALL = "sort-all"
    UNIQUE = "unique"

    @classmethod
    def get_set(cls) -> set:
        ok = set([val for val in cls.__dict__.keys() if val.isupper()])
        return ok


class Commands(utils.HasPrettyRepr):
    # features usable in parser_v1
    mask = False
    random = False
    sort = False
    sort_all = False
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
    method = "lexicographical"

    def get_logger_level(self) -> int:
        return logging.DEBUG if self.verbose else logging.INFO

    def debug(self) -> None:
        pprint.pprint(self, utils.debug_fp)

    @classmethod
    def prepare_parser(cls) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="sanipro",
            description=(
                "Toolbox for Stable Diffusion prompts. "
                "'Sanipro' stands for 'pro'mpt 'sani'tizer."
            ),
            epilog="Helps for subcommands are available, respectively.",
        )

        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help=(
                "Switch to display the extra logs for nerds, "
                "This may be useful for debugging."
            ),
        )

        parser.add_argument(
            "-d",
            "--input-delimiter",
            metavar="str",
            default=cls.input_delimiter,
            help=(
                "Delimiter character for the original prompts."
                "(default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-s",
            "--output-delimiter",
            metavar="str",
            default=cls.output_delimiter,
            help=(
                "Delimiter character for the processed prompts"
                "(default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-p",
            "--ps1",
            metavar="str",
            default=cls.ps1,
            help=(
                "Custom string that is used when asking user "
                "for the prompts (default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Provides REPL interface to play with prompts.",
        )

        parser.add_argument(
            "-u",
            "--roundup",
            metavar="n",
            default=cls.roundup,
            type=int,
            help=(
                "All the token with weights (> 1.0 or < 1.0) "
                "will be rounded up to n digit(s) in here (default: `%(default)s`)"
            ),
        )

        parser.add_argument(
            "-x",
            "--exclude",
            metavar="str",
            nargs="*",
            help=(
                "Exclude this token from original prompt. "
                "Multiple options can be specified."
            ),
        )

        parser.add_argument(
            "--use-parser-v2",
            "-2",
            action="store_true",
            help=(
                "Switch to use another version of the parser instead. "
                "This might be inferrior to the default parser "
                "as it only parses the prompt and does nothing at all."
            ),
        )

        subparsers = parser.add_subparsers(
            title="Subcommands",
            description=(
                "List of available filters that can be applied to the prompt."
            ),
            dest="subcommand",
            help=("Just one filter can be applied at once."),
            metavar="FILTER",
        )

        parser_mask = subparsers.add_parser(
            Subcommand.MASK,
            help="mask tokens",
            description="Mask words specified with another word (optional).",
            epilog=(
                "This subcommands allow this program to remove the tokens"
                "rather than remove them as in `--exclude` option. "
                "Still, you can use `--exclude` option as well as this method."
            ),
        )

        parser_mask.add_argument(
            "mask",
            nargs="*",
            help="Masks this word.",
        )

        parser_mask.add_argument(
            "-t",
            "--replace-to",
            default=cls.replace_to,
            help="The new character or string replaced to.",
        )

        parser_random = subparsers.add_parser(
            Subcommand.RANDOM,
            help="Shuffles all the prompts altogether.",
            description="Shuffles all the prompts altogether.",
        )

        parser_sort = subparsers.add_parser(
            Subcommand.SORT,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )
        parser_sort.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="with reversed order",
        )

        parser_sort_all = subparsers.add_parser(
            Subcommand.SORT_ALL,
            help="Reorder all the prompts.",
            description="Reorder all the prompts.",
            epilog="METHOD = { " + ", ".join(sort_all_factory.available) + " }",
        )

        parser_sort_all.add_argument(
            "-m",
            "--method",
            default=cls.method,
            const=cls.method,
            nargs="?",
            help="based on this strategy (default: `%(default)s`)",
        )

        parser_sort_all.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="with reversed order",
        )

        parser_unique = subparsers.add_parser(
            Subcommand.UNIQUE,
            help="removes duplicated tokens, and uniquify them",
            description="Removes duplicated tokens, and uniquify them.",
            epilog="",
        )

        parser_unique.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="make the token with the heaviest weight survived",
        )

        return parser

    @property
    def get_delimiter(self) -> Delimiter:
        return Delimiter(
            self.input_delimiter,
            self.output_delimiter,
        )

    def get_builder_from(self, use_parser_v2: bool) -> PromptBuilder:
        delim = self.get_delimiter
        if not use_parser_v2:
            return delim.create_builder(PromptBuilderV1)
        return delim.create_builder(PromptBuilderV2)

    def get_builder(self) -> PromptBuilder:
        cfg = FuncConfig

        if self.use_parser_v2 and self.subcommand in Subcommand.get_set():
            raise NotImplementedError(
                f"the '{self.subcommand}' command is not available "
                "when using parse_v2."
            )

        if self.use_parser_v2:
            logger.warning("using parser_v2.")

        builder = self.get_builder_from(self.use_parser_v2)
        # always round
        builder.append_hook(
            cfg(
                func=filters.round_up,
                kwargs={"digits": self.roundup},
            ),
        )

        if self.subcommand == Subcommand.RANDOM:
            builder.append_hook(
                cfg(
                    func=filters.random,
                    kwargs={},
                ),
            )

        if self.subcommand == Subcommand.SORT_ALL:
            from . import sort_all_factory

            sorted_partial = sort_all_factory.apply_from(self.method)
            builder.append_hook(
                cfg(
                    func=filters.sort_all,
                    kwargs={
                        "sorted_partial": sorted_partial,
                        "reverse": True if (self.reverse or False) else False,
                    },
                )
            )

        if self.subcommand == Subcommand.SORT:
            builder.append_hook(
                cfg(
                    func=filters.sort,
                    kwargs={
                        "reverse": (self.reverse or False),
                    },
                )
            )

        if self.subcommand == Subcommand.UNIQUE:
            builder.append_hook(
                cfg(
                    func=filters.unique,
                    kwargs={
                        "reverse": self.reverse or False,
                    },
                )
            )

        if self.subcommand == Subcommand.MASK:
            builder.append_hook(
                cfg(
                    func=filters.mask,
                    kwargs={
                        "excludes": self.mask,
                        "replace_to": self.replace_to,
                    },
                )
            )

        if self.exclude:
            builder.append_hook(
                cfg(
                    func=filters.exclude,
                    kwargs={
                        "excludes": self.exclude,
                    },
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
        raise NotImplementedError

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


class RunnerInteractive(Runner, InteractiveConsole):
    def __init__(
        self,
        builder: PromptBuilder,
        ps1: str,
        prpt: type[TokenInterface],
    ):
        self.builder = builder
        self.ps1 = ps1
        self.prpt = prpt

        InteractiveInterpreter.__init__(self)
        self.filename = "<console>"
        self.local_exit = False
        self.resetbuffer()

    def run(self):
        cli_hooks.execute(cli_hooks.interactive)
        self.interact()

    def interact(self, banner=None, exitmsg=None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = self.ps1

        if banner is None:
            self.write(
                f"Sanipro (created by iigau) in interactive mode\n"
                f"Program was launched up at {time.asctime()}.\n"
            )
        elif banner:
            self.write("%s\n" % str(banner))

        try:
            while True:
                try:
                    prompt = sys.ps1
                    try:
                        line = self.raw_input(prompt)  # type: ignore
                    except EOFError:
                        break
                    else:
                        self.push(line)
                except ValueError as e:
                    logger.exception(f"error: {e}")
                except (IndexError, KeyError, AttributeError) as e:
                    logger.exception(f"error: {e}")
                except KeyboardInterrupt:
                    self.resetbuffer()
                    break

        finally:
            if exitmsg is None:
                self.write("\n")
            elif exitmsg != "":
                self.write("%s\n" % exitmsg)

    def runcode(self, code):
        print(code)

    def runsource(self, source, filename="<input>", symbol="single"):
        self.builder.parse(
            str(source),
            self.prpt,
            auto_apply=True,
        )
        result = str(self.builder)
        self.runcode(result)  # type: ignore
        return False

    def push(self, line, filename=None, _symbol="single"):
        self.buffer.append(line)
        source = "\n".join(self.buffer)
        if filename is None:
            filename = self.filename
        more = self.runsource(source, filename, symbol=_symbol)
        if not more:
            self.resetbuffer()
        return more


class RunnerNonInteractive(Runner):
    def _run_once(self) -> None:
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
        self._run_once()


def app():
    try:
        args = Commands.from_sys_argv(sys.argv[1:])
        cli_hooks.execute(cli_hooks.init)
        logger_root.setLevel(args.get_logger_level())
        args.debug()
        runner = Runner.from_args(args)
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
