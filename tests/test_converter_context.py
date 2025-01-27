import unittest

from sanipro.converter_context import (
    A1111Config,
    Config,
    ConfigError,
    CSVConfig,
    InputConfig,
    OutputConfig,
    config_from_str,
)


class Testconfig_load_from_yaml(unittest.TestCase):
    def test_basic_cases(self) -> None:
        test_cases = (
            (
                r"""
a1111:
  input:
    token_separator: ","
  output:
    token_separator: "\n, "

a1111_compat:
  input:
    token_separator: ","
  output:
    token_separator: "\n, "

csv:
  input:
    token_separator: "\n"
    field_separator: "\t"
  output:
    token_separator: "\n"
    field_separator: "@"
""",
                Config(
                    A1111Config(InputConfig(","), OutputConfig("\n, ")),
                    A1111Config(InputConfig(","), OutputConfig("\n, ")),
                    CSVConfig(InputConfig("\n", "\t"), OutputConfig("\n", "@")),
                ),
            ),
        )

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = config_from_str(input_text)
                self.assertEqual(result, expected)

    def test_error_cases(self) -> None:
        test_cases = (
            # unsatisfied number of sections, just csv
            r"""
csv:
  input:
    token_separator: "\n"
    field_separator: "\t"
  output:
    token_separator: "\n"
    field_separator: "@"
""",
            r"""
a1111:
  input:
    token_separator: ","
  output:
    token_separator: "\n, "

a1111_compat:
  input:
    token_separator: ","
  output:
    token_separator: "\n, "

csv:
  input:
    token_separator: "\n"
    # field_separator: "\t"
  output:
    token_separator: "\n"
    field_separator: "@"
""",
        )

        for input_text in test_cases:
            with self.subTest(input_text=input_text):
                with self.assertRaises(ConfigError):
                    config_from_str(input_text)


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config(
            A1111Config(InputConfig(","), OutputConfig(", ")),
            A1111Config(InputConfig(","), OutputConfig(", ")),
            CSVConfig(InputConfig("\n", "\t"), OutputConfig("\n", "\t")),
        )
        super().setUp()

    def test_get(self) -> None:
        self.assertEqual(
            self.config.get("a1111"), A1111Config(InputConfig(","), OutputConfig(", "))
        )
        with self.assertRaises(KeyError):
            self.config.get("key")

    def test_get_input_token_separator(self) -> None:
        test_cases = [("a1111", ","), ("csv", "\n")]

        for key, expected in test_cases:
            self.assertEqual(self.config.get_input_token_separator(key), expected)

    def test_get_output_token_separator(self) -> None:
        test_cases = [("a1111", ", "), ("csv", "\n")]

        for key, expected in test_cases:
            self.assertEqual(self.config.get_output_token_separator(key), expected)

    def test__get_input_field_separator(self) -> None:
        test_cases = [("a1111", None), ("csv", "\t")]

        for key, expected in test_cases:
            self.assertEqual(self.config._get_input_field_separator(key), expected)

    def test__get_output_field_separator(self) -> None:
        test_cases = [("a1111", None), ("csv", "\t")]

        for key, expected in test_cases:
            self.assertEqual(self.config._get_output_field_separator(key), expected)
