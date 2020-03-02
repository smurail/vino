import re

from functools import reduce


def compose(*functions):
    functions = [f for f in functions if callable(f)]

    def inner(arg):
        return reduce(lambda arg, func: func(arg), functions, arg)
    return inner


NO_DEFAULT = object()


def cast(value, to_type, default=NO_DEFAULT):
    try:
        if isinstance(value, to_type):
            return value
        return to_type(value)
    except (ValueError, TypeError):
        return to_type() if default is NO_DEFAULT else default


DIGITS = re.compile(r'\d+|$')


def to_int(value: str):
    # XXX DIGITS regex match digits or empty string (because of |$ part)
    match = DIGITS.search(value).group()  # type: ignore
    return cast(match, int)
