import re


DIGITS = re.compile(r'\d+')


def to_int(value: str) -> int:
    # XXX DIGITS regex match digits or empty string (because of |$ part)
    match = DIGITS.search(value)
    return int(match.group()) if match else 0
