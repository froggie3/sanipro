#!/usr/bin/env python3

from .common import Tokens, Prompt, PromptList, Sentence, read_char
import logging

logger = logging.getLogger()

def extract_token(sentence: Sentence):
    """カッコを外して word:1.2 のような組を得る"""
    stack = []
    character_stack = []

    for character in sentence:
        if character == Tokens.PARENSIS_LEFT:
            stack.append(character)
        elif character == Tokens.PARENSIS_RIGHT:
            stack.pop()
        elif character == Tokens.COMMA:
            if stack:
                read_char(character_stack, character)
                continue
            element = "".join(character_stack)
            character_stack = []
            yield element
        else:
            read_char(character_stack, character)


def parse(sentence: Sentence) -> PromptList:
    """
    カッコの中身は反応しない .split() メソッドのような動作
    (emphasis:1.2) <- strip で左辺と右辺を分割、
    3 つ以上の要素になったら最後のコロンで区切られた右側を強さとして採択
    """
    result = PromptList()

    for token_conbined in extract_token(sentence):
        token = token_conbined.strip().split(Tokens.COLON)
        length_token = len(token)
        cursor = Prompt() 

        if length_token == 1:
            cursor._name, = token
        elif length_token == 2:
            cursor._name, cursor._strength = token
        else:
            *ret, cursor._strength = token
            cursor._name = Tokens.COLON.join(ret)

        result.append(cursor)

    return result
