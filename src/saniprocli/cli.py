import logging
import sys

from saniprocli.cli_demo import DemoCommands
from saniprocli.cli_runner import Runner

from . import cli_hooks

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


def app():
    try:
        args = DemoCommands.from_sys_argv(sys.argv[1:])
        cli_hooks.execute(cli_hooks.init)

        log_level = args.get_logger_level()
        logger_root.setLevel(log_level)

        args.debug()
        runner = Runner.from_args(args)
        runner.run()
    except Exception as e:
        logger.exception(f"error: {e}")
    finally:
        sys.exit(1)
