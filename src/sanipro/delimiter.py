import logging
import typing

logger = logging.getLogger(__name__)


class Delimiter(typing.NamedTuple):
    sep_input: str
    sep_output: str
