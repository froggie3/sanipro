import typing
from dataclasses import dataclass
from typing import Callable, Optional

import yaml

from sanipro.abc import IPromptTokenizer, TokenInterface
from sanipro.parser import CSVParser, NormalParser
from sanipro.pipeline_v1 import A1111Parser, A1111Tokenizer
from sanipro.token import A1111Token, CSVToken
from sanipro.tokenizer import SimpleTokenizer


@dataclass
class InputConfig:
    """The input section of the config file specification."""

    token_separator: str
    field_separator: Optional[str] = None


@dataclass
class OutputConfig:
    """The output section of the config file specification."""

    token_separator: str
    field_separator: Optional[str] = None


@dataclass
class A1111Config:
    """The a1111 section of the config file specification."""

    input: InputConfig
    output: OutputConfig


@dataclass
class CSVConfig:
    """The csv section of the config file specification."""

    input: InputConfig
    output: OutputConfig


@dataclass
class TokenMap:
    """A couple of infomation to tokenize a token."""

    type_name: str
    token_type: type[TokenInterface]
    field_separator: str
    formatter: Callable
    tokenizer: type[IPromptTokenizer]
    parser: type[NormalParser]


@dataclass
class Config:
    """Represents config file specification."""

    a1111: A1111Config
    csv: CSVConfig

    def get(self, key: str):
        """Returns the section corresponded to key parameter."""

        try:
            return getattr(self, key)
        except AttributeError:
            raise AttributeError(f"failed to retrieve the config")

    def get_input_token_separator(self, key: str) -> str:
        """The input token separator from the name of corresponded key type."""
        _config = self

        return _config.get(key).input.token_separator

    def get_output_token_separator(self, key: str) -> str:
        """The output token separator from the name of corresponded key type."""
        _config = self

        return _config.get(key).output.token_separator

    def _get_input_field_separator(self, key: str) -> str:
        """The input field separator from the name of corresponded key type."""
        _config = self

        return _config.get(key).input.field_separator

    def _get_output_field_separator(self, key: str) -> str:
        """The output field separator from the name of corresponded key type."""
        _config = self

        return _config.get(key).output.field_separator

    def _get_token_map_mixin(self, field_separator: str) -> dict[str, TokenMap]:
        return {
            "a1111": TokenMap(
                type_name="a1111",
                token_type=A1111Token,
                field_separator=field_separator,
                formatter=format_a1111_token,
                tokenizer=A1111Tokenizer,
                parser=A1111Parser,
            ),
            "csv": TokenMap(
                type_name="csv",
                token_type=CSVToken,
                field_separator=field_separator,
                formatter=format_csv_token,
                tokenizer=SimpleTokenizer,
                parser=CSVParser,
            ),
        }

    def get_input_token_class(self, key: str) -> TokenMap:
        """Get the input token type from the name of corresponded key type."""

        field_separator = self._get_input_field_separator(key)
        token_map = self._get_token_map_mixin(field_separator)

        return token_map[key]

    def get_output_token_class(self, key: str) -> TokenMap:
        """Get the output token type from the name of corresponded key type."""

        field_separator = self._get_output_field_separator(key)
        token_map = self._get_token_map_mixin(field_separator)

        return token_map[key]


def config_load_from_yaml(yaml_data: typing.Any) -> Config:
    """Load config from the read YAML data."""

    a1111 = A1111Config(
        InputConfig(yaml_data["a1111"]["input"]["token_separator"]),
        OutputConfig(yaml_data["a1111"]["output"]["token_separator"]),
    )
    csv = CSVConfig(
        InputConfig(
            yaml_data["csv"]["input"]["token_separator"],
            yaml_data["csv"]["input"]["field_separator"],
        ),
        OutputConfig(
            yaml_data["csv"]["output"]["token_separator"],
            yaml_data["csv"]["output"]["field_separator"],
        ),
    )

    return Config(a1111, csv)


def config_from_file(file_path: str) -> Config:
    """Read config from a file path."""

    with open(file_path, "r") as stream:
        data_loaded = yaml.safe_load(stream)
        return config_load_from_yaml(data_loaded)


def config_from_str(data: str) -> Config:
    """Read config directly from the string."""

    data_loaded = yaml.safe_load(data)
    return config_load_from_yaml(data_loaded)


def get_config(file_path: str | None = None) -> Config:
    """Get a config from filepath. The default config is returned
    if None is specified."""

    if file_path is None:
        return Config(
            A1111Config(InputConfig(","), OutputConfig(", ")),
            CSVConfig(InputConfig("\n", "@"), OutputConfig("\n", " ")),
        )
    else:
        return config_from_file(file_path)


def format_a1111_token(token: A1111Token) -> str:
    """Callback function to format a A1111Token."""

    if token.weight != 1.0:
        return f"({token.name}:{token.weight})"

    return token.name


def format_csv_token(field_separator: str) -> Callable:
    """Callback function to format a CSVToken."""

    def f(token: CSVToken) -> str:
        return f"{token.name}{field_separator}{token.weight}"

    return f
