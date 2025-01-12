import typing


class Delimiter(typing.NamedTuple):
    """Delimiter class."""

    sep_input: str
    sep_output: str
    sep_field: str | None = None
