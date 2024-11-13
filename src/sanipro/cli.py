import logging
import sys

from . import cli_hooks
from .cli_runner import Runner
from .commands import Commands

logger_root = logging.getLogger()
logger = logging.getLogger(__name__)


def app():
    try:
        args = Commands.from_sys_argv(sys.argv[1:])
        cli_hooks.execute(cli_hooks.init)

        log_level = args.get_logger_level()
        logger_root.setLevel(log_level)

        args.debug()
        runner = Runner.from_args(args)
        runner.run()
    except (KeyboardInterrupt, EOFError) as e:
        print()
        sys.exit(1)
    except (ValueError, NotImplementedError) as e:
        logger.error(f"error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"error: {e}")
        sys.exit(1)
