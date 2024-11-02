import logging

from .common import PromptInterface

logger = logging.getLogger()


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


def collect_same_prompt(prompts: list[PromptInterface]):
    u: dict[str, list[PromptInterface]] = {}
    for prompt in prompts:
        if prompt.name in u:
            u[prompt.name].append(prompt)
        else:
            u[prompt.name] = [prompt]
    return u


def sort(prompts: list[PromptInterface], reverse=False) -> list[PromptInterface]:
    """
    >>> from lib.common import PromptInteractive
    >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
    >>> [(x.name, x.strength) for x in p]
    [('white hair', 1.0), ('white hair', 1.2)]

    >>> from lib.common import PromptInteractive
    >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
    >>> [(x.name, x.strength) for x in p]
    [('white hair', 1.2), ('white hair', 1.0)]
    """
    u = collect_same_prompt(prompts)

    prompts = []
    for k, v in u.items():
        v.sort(key=lambda x: x.strength, reverse=reverse)
        for item in v:
            prompts.append(item)

    return prompts


def unique(prompts: list[PromptInterface], reverse=False) -> list[PromptInterface]:
    """
    >>> from lib.common import PromptInteractive
    >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
    >>> [(x.name, x.strength) for x in p]
    [('white hair', 1.0)]

    >>> from lib.common import PromptInteractive
    >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
    >>> [(x.name, x.strength) for x in p]
    [('white hair', 1.2)]
    """
    u = collect_same_prompt(prompts)

    prompts = []
    for k, v in u.items():
        v.sort(key=lambda x: x.strength, reverse=reverse)
        prompts.append(v.pop(0))

    return prompts
