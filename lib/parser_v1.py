#!/usr/bin/env python3

from pprint import pprint
from .common import Prompt, Tokens, Cursor, Sentence, read_char
import logging

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
# logger.level = logging.INFO
logger.level = logging.DEBUG


def parse(str):
    result = []
    stack = []
    sentence = Sentence(str)
    is_strength = False
    cursor = Cursor.new()

    for character in sentence:
        if character == Tokens.PARENSIS_LEFT:
            stack.append(character)
        elif character == Tokens.PARENSIS_RIGHT:
            is_strength = False
            stack.pop()
        elif character == Tokens.COLON:
            is_strength = True
        elif character == Tokens.COMMA:
            if stack:
                read_char(cursor._name, character)
                continue
            result.append(cursor)
            cursor = Cursor.new()
        elif character != Tokens.SPACE:
            if is_strength:
                read_char(cursor._strength, character)
            else:
                read_char(cursor._name, character)
        elif character == Tokens.SPACE:
            read_char(cursor._name, character)

        logger.debug(f"{character=}, {stack=}")

    # pprint(result)
    return result
