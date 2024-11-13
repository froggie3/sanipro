import dataclasses
import logging
import pprint
import sys
import time
from code import InteractiveConsole, InteractiveInterpreter

from . import cli_hooks, filters, utils
from .abc import TokenInterface
from .commands import Commands
from .common import MutablePrompt, PromptBuilder
from .parser import TokenInteractive, TokenNonInteractive

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


class Runner(utils.HasPrettyRepr):
    def __init__(
        self,
        builder: PromptBuilder,
        ps1: str,
        prpt: type[TokenInterface],
    ) -> None:
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


class Analyzer:
    pass


@dataclasses.dataclass
class AnalyzerDiff(Analyzer):
    before_process: MutablePrompt
    after_process: MutablePrompt

    @property
    def len_reduced(self) -> int:
        return len(self.before_process) - len(self.after_process)

    @property
    def duplicates(self) -> MutablePrompt:
        tokens_pairs = []
        for _, tokens in filters.collect_same_prompt_generator(self.before_process):
            if len(tokens) > 1:
                pair = []
                for token in tokens:
                    stats = {
                        "token": token,
                        # "hash": hash(token),
                        # "id": hex(id(token)),
                    }
                    pair.append(stats)
                tokens_pairs.append({"pair": pair})
        for pair in tokens_pairs:
            pprint.pprint(pair, utils.debug_fp)
            # logger.debug(token)
        return tokens_pairs

    def get_stats(self) -> dict[str, dict[str, int]]:
        self.duplicates
        stats_number = {
            "statistics": {
                "before_process": len(self.before_process),
                "after_process": len(self.after_process),
                "reduced_total": self.len_reduced,
            }
        }
        return stats_number


class RunnerInteractive(Runner, InteractiveConsole):
    def __init__(
        self,
        builder: PromptBuilder,
        ps1: str,
        prpt: type[TokenInterface],
    ) -> None:
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
        tokens_unparsed = self.builder.parse(
            str(source),
            self.prpt,
            auto_apply=True,
        )
        tokens = str(self.builder)

        anal = AnalyzerDiff(tokens_unparsed, self.builder.tokens)
        pprint.pprint(anal.get_stats(), utils.debug_fp)

        self.runcode(tokens)  # type: ignore
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
