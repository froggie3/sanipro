import logging
from typing import Any, Callable, Generator, Type, TypedDict

from .common import PromptInterface, Sentence, Tokens, read_char

logger = logging.getLogger()


class FuncConfig(TypedDict):
    # func: Callable[...]
    func: Callable
    kwargs: dict[str, Any]


def extract_token(sentence: Sentence) -> Generator[str, None, None]:
    """
    split `sentence` at commas and remove parentheses.

    >>> list(extract_token('1girl,'))
    ['1girl']
    >>> list(extract_token('(brown hair:1.2),'))
    ['brown hair:1.2']
    >>> list(extract_token('1girl, (brown hair:1.2), school uniform, smile,'))
    ['1girl', 'brown hair:1.2', 'school uniform', 'smile']
    """
    stack = []
    character_stack = []

    for character in sentence:
        match (character):
            case Tokens.PARENSIS_LEFT:
                stack.append(character)
            case Tokens.PARENSIS_RIGHT:
                stack.pop()
            case Tokens.COMMA:
                if stack:
                    read_char(character_stack, character)
                    continue
                element = "".join(character_stack).strip()
                character_stack = []
                yield element
            case _:
                read_char(character_stack, character)


def parse_line(token_combined: str, factory: Type[PromptInterface]) -> PromptInterface:
    """
    split `token_combined` into left and right sides with `:`
    when there are three or more elements,
    the right side separated by the last colon is adopted as the strength.

    >>> from lib.common import PromptInteractive, PromptNonInteractive

    >>> parse_line('brown hair:1.2', PromptInteractive)
    PromptInteractive(_name='brown hair', _strength='1.2', _delimiter=':')

    >>> parse_line('1girl', PromptInteractive)
    PromptInteractive(_name='1girl', _strength='1.0', _delimiter=':')

    >>> parse_line('brown:hair:1.2', PromptInteractive)
    PromptInteractive(_name='brown:hair', _strength='1.2', _delimiter=':')
    """
    token = token_combined.split(Tokens.COLON)

    match (len(token)):
        case 1:
            name, *_ = token
            return factory(name, "1.0")
        case 2:
            name, strength, *_ = token
            return factory(name, strength)
        case _:
            *ret, strength = token
            name = Tokens.COLON.join(ret)
            return factory(name, strength)


def mask(prompts: list[PromptInterface], excludes: list[str]) -> list[PromptInterface]:
    """
    >>> from lib.common import PromptInteractive
    >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
    >>> [x.name for x in p]
    ['%%%', 'thighhighs']
    """
    filtered_prompts = []
    for prompt in prompts:
        for excluded in excludes:
            if excluded in prompt.name:
                filtered_prompts.append(prompt.replace("%%%"))
                break
        else:
            filtered_prompts.append(prompt)

    return filtered_prompts


def exclude(
    prompts: list[PromptInterface], excludes: list[str]
) -> list[PromptInterface]:
    """
    >>> from lib.common import PromptInteractive
    >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
    >>> [x.name for x in p]
    ['thighhighs']
    """
    filtered_prompts = []
    for prompt in prompts:
        for excluded in excludes:
            if excluded not in prompt.name:
                filtered_prompts.append(prompt)
                break
        else:
            continue

    return filtered_prompts


def sort(prompts: list[PromptInterface], reverse=False) -> list[PromptInterface]:
    """
    >>> from lib.common import PromptInteractive
    >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
    >>> [(x.name, x.strength) for x in p]
    [('white hair', 1.0), ('white hair', 1.2)]
    """
    u: dict[str, list[PromptInterface]] = {}
    for prompt in prompts:
        if prompt.name in u:
            u[prompt.name].append(prompt)
        else:
            u[prompt.name] = [prompt]

    prompts = []
    for k, v in u.items():
        v.sort(key=lambda x: x.strength, reverse=reverse)
        for item in v:
            prompts.append(item)

    return prompts


def apply(
    prompts: list[PromptInterface], funcs: list[FuncConfig]
) -> list[PromptInterface]:
    for func in funcs:
        prompts = func["func"](prompts, **func["kwargs"])
    return prompts


def parse(sentence: Sentence, factory: Type[PromptInterface]) -> list[PromptInterface]:
    prompts = list()

    for element in extract_token(sentence):
        prompt = parse_line(element, factory)
        prompts.append(prompt)

    return prompts
