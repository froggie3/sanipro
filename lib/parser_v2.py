#!/usr/bin/env python3

import logging

from .common import (
    PromptList,
    Sentence,
    Tokens,
    read_char,
    PromptClass,
)

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


def parse_line(token_combined: str, Class: PromptClass):
    """
    カッコの中身は反応しない .split() メソッドのような動作
    (emphasis:1.2) <- strip で左辺と右辺を分割、
    3 つ以上の要素になったら最後のコロンで区切られた右側を強さとして採択
    """
    token = token_combined.strip().split(Tokens.COLON)
    length_token = len(token)

    prompt = Class()

    if length_token == 1:
        prompt._name, = token
    elif length_token == 2:
        prompt._name, prompt._strength = token
    else:
        *ret, prompt._strength = token
        prompt._name = Tokens.COLON.join(ret)

    return prompt


def parse(sentence: Sentence, Class: PromptClass) -> PromptList:
    prompts = PromptList()

    for element in extract_token(sentence):
        prompt = parse_line(element, Class)
        prompts.append(prompt)

    return prompts
