import functools

from .abc import TokenInterface

available = (
    "lexicographical",
    "length",
    "strength",
)


def sort_lexicographically(token: TokenInterface) -> str:
    return token.name


def sort_by_length(token: TokenInterface) -> int:
    return token.length


def sort_by_strength(token: TokenInterface) -> str:
    return token.strength


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
