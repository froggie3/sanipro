import typing
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import yaml

from sanipro.abc import IPromptTokenizer, TokenInterface
from sanipro.parser import CSVParser, NormalParser
from sanipro.pipeline_v1 import A1111Parser, A1111Tokenizer
from sanipro.token import A1111Token, CSVToken
from sanipro.tokenizer import SimpleTokenizer


class ConfigError(Exception):
    """Raises this error when the property of the config is unrecognizable,
    missing, not found, and so on."""

    def __init__(self, path: str | None = None, *args: object) -> None:
        super().__init__(*args)
        self.path = path


class SupportedTokenType(Enum):
    """Supported token types."""

    A1111 = "a1111"
    CSV = "csv"

    @staticmethod
    def choises() -> list[str]:
        return [item.value for item in SupportedTokenType]


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
        except AttributeError as e:
            raise type(e)(self._error_bad_keyname(key))

    def get_input_token_separator(self, key: str) -> str:
        """The input token separator from the name of corresponded key type."""

        return self.get(key).input.token_separator

    def get_output_token_separator(self, key: str) -> str:
        """The output token separator from the name of corresponded key type."""

        return self.get(key).output.token_separator

    def _get_input_field_separator(self, key: str) -> str:
        """The input field separator from the name of corresponded key type."""

        return self.get(key).input.field_separator

    def _get_output_field_separator(self, key: str) -> str:
        """The output field separator from the name of corresponded key type."""

        return self.get(key).output.field_separator

    def _get_token_map_mixin(self, field_separator: str) -> dict[str, TokenMap]:
        """Generate a template of token map from field separator."""

        return {
            "a1111": TokenMap(
                SupportedTokenType.A1111.value,
                A1111Token,
                field_separator,
                format_a1111_token,
                A1111Tokenizer,
                A1111Parser,
            ),
            "csv": TokenMap(
                SupportedTokenType.CSV.value,
                CSVToken,
                field_separator,
                format_csv_token,
                SimpleTokenizer,
                CSVParser,
            ),
        }

    def _error_bad_keyname(self, bad_key_name: str) -> str:
        """Error message template."""

        return f"unsupported token type was supplied: {bad_key_name}"

    def get_input_token_class(self, key: str) -> TokenMap:
        """Get the input token type from the name of corresponded key type."""

        field_separator = self._get_input_field_separator(key)
        token_map = self._get_token_map_mixin(field_separator)

        try:
            return token_map[key]
        except KeyError as e:
            raise type(e)(self._error_bad_keyname(key))

    def get_output_token_class(self, key: str) -> TokenMap:
        """Get the output token type from the name of corresponded key type."""

        field_separator = self._get_output_field_separator(key)
        token_map = self._get_token_map_mixin(field_separator)

        try:
            return token_map[key]
        except KeyError as e:
            raise type(e)(self._error_bad_keyname(key))


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


def config_from_file(path: str) -> Config:
    """Read config from a file path."""

    try:
        with open(path, "r") as stream:
            data_loaded = yaml.safe_load(stream)
            return config_load_from_yaml(data_loaded)
    except Exception:
        raise ConfigError(path=path)


def config_from_str(data: str) -> Config:
    """Read config directly from the string."""

    data_loaded = yaml.safe_load(data)
    try:
        return config_load_from_yaml(data_loaded)
    except Exception:
        raise ConfigError


def get_config(path: str | None = None) -> Config:
    """Get a config from filepath. The default config is returned
    if None is specified."""

    if path is None:
        a1111 = A1111Config(InputConfig(","), OutputConfig(", "))
        csv = CSVConfig(InputConfig("\n", "\t"), OutputConfig("\n", "\t"))
        return Config(a1111, csv)

    return config_from_file(path)


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
