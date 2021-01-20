import re
import unicodedata

from functools import reduce


def compose(*functions):
    functions = [f for f in functions if callable(f)]

    def inner(arg):
        return reduce(lambda arg, func: func(arg), functions, arg)
    return inner


NO_DEFAULT = object()


def cast(to_type, value, default=NO_DEFAULT):
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
    return cast(int, match)


# XXX Borrowed from django.utils.text (we don't want vino.core to depend on
#     Django)
def slugify(value: str) -> str:
    """
    Convert spaces to hyphens. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace.
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
