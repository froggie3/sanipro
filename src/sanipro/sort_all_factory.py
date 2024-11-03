import functools

from .abc import PromptInterface

available = (
    "lexicographical",
    "length",
    "strength",
)


def sort_lexicographically(prompt: PromptInterface) -> str:
    return prompt.name


def sort_by_length(prompt: PromptInterface) -> int:
    return prompt.length


def sort_by_strength(prompt: PromptInterface) -> str:
    return prompt.strength


def apply_from(sort_law_name: str):
    funcs = (
        sort_lexicographically,
        sort_by_length,
        sort_by_strength,
    )

    for func_name, func in zip(available, funcs):
        if func_name.startswith(sort_law_name):
            return functools.partial(sorted, key=func)
    else:
        raise Exception(f"no matched sort law for '{sort_law_name}'")
