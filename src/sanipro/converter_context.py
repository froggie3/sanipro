import typing
from dataclasses import dataclass
from typing import Callable, Optional

from sanipro.abc import IPromptTokenizer, TokenInterface
from sanipro.parser import CSVParser, NormalParser
from sanipro.parser_a1111 import A1111Parser
from sanipro.pipeline_v1 import A1111Tokenizer
from sanipro.token import (
    A1111Token,
    CSVToken,
    format_a1111_compat_token,
    format_a1111_token,
    format_csv_token,
)
from sanipro.tokenizer import SimpleTokenizer


class ConfigError(Exception):
    """Raises this error when the property of the config is unrecognizable,
    missing, not found, and so on."""

    def __init__(self, path: str | None = None, *args: object) -> None:
        super().__init__(*args)
        self.path = path


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
    a1111_compat: A1111Config
    csv: CSVConfig

    def get(self, key: str):
        """Returns the section corresponded to key parameter."""

        name_conv = {"a1111": "a1111", "a1111compat": "a1111_compat", "csv": "csv"}

        try:
            resolved = name_conv[key]
        except KeyError as e:
            raise type(e)(self._error_bad_keyname(key))

        return getattr(self, resolved)

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

    def _error_bad_keyname(self, bad_key_name: str) -> str:
        """Error message template."""

        return f"unsupported token type was supplied: {bad_key_name}"

    def get_input_token_class(self, key: str) -> TokenMap:
        """Get the input token type from the name of corresponded key type."""

        field_separator = self._get_input_field_separator(key)
        # dict_key = option value
        # dict_value = key name of the config
        token_map = {
            "a1111compat": TokenMap(
                "a1111_compat",
                A1111Token,
                field_separator,
                format_a1111_token,
                A1111Tokenizer,
                A1111Parser,
            ),
            "csv": TokenMap(
                "csv",
                CSVToken,
                field_separator,
                format_csv_token,
                SimpleTokenizer,
                CSVParser,
            ),
        }

        try:
            return token_map[key]
        except KeyError as e:
            raise type(e)(self._error_bad_keyname(key))

    def get_output_token_class(self, key: str) -> TokenMap:
        """Get the output token type from the name of corresponded key type."""

        field_separator = self._get_output_field_separator(key)
        token_map = {
            "a1111": TokenMap(
                "a1111",
                A1111Token,
                field_separator,
                format_a1111_token,
                A1111Tokenizer,
                A1111Parser,
            ),
            "a1111compat": TokenMap(
                "a1111_compat",
                A1111Token,
                field_separator,
                format_a1111_compat_token,
                A1111Tokenizer,
                A1111Parser,
            ),
            "csv": TokenMap(
                "csv",
                CSVToken,
                field_separator,
                format_csv_token,
                SimpleTokenizer,
                CSVParser,
            ),
        }

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
    a1111_compat = A1111Config(
        InputConfig(yaml_data["a1111_compat"]["input"]["token_separator"]),
        OutputConfig(yaml_data["a1111_compat"]["output"]["token_separator"]),
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
    return Config(a1111, a1111_compat, csv)


def config_from_file(path: str) -> Config:
    """Read config from a file path."""

    import yaml

    try:
        with open(path, "r") as stream:
            data_loaded = yaml.safe_load(stream)
            return config_load_from_yaml(data_loaded)
    except Exception:
        raise ConfigError(path=path)


def config_from_str(data: str) -> Config:
    """Read config directly from the string."""

    import yaml

    data_loaded = yaml.safe_load(data)
    try:
        return config_load_from_yaml(data_loaded)
    except Exception:
        raise ConfigError
