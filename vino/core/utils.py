import re
import unicodedata

from typing import Type, TypeVar, Any


T = TypeVar('T', bound=int)


def cast(to_type: Type[T], value: Any) -> T:
    try:
        if isinstance(value, to_type):
            return value
        return to_type(value)
    except (ValueError, TypeError):
        return to_type()


DIGITS = re.compile(r'\d+|$')


def to_int(value: str) -> int:
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
