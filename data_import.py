#!/usr/bin/env python
import django
from django.conf import settings

django.setup()

import re
import csv

from io import StringIO
from functools import partial

from vino.sharekernel.models import ViabilityProblem as VP, Data


NO_DEFAULT = object()


def cast(value, to_type, default=NO_DEFAULT):
    try:
        if type(value) is to_type:
            return value
        return to_type(value)
    except ValueError:
        return to_type() if default is NO_DEFAULT else default


def Tuple(typ, sep=','):
    def parser(inp):
        return [cast(item.strip(), typ) for item in inp.split(sep)]
    return parser


SPACES = re.compile(r' +')
TOKENS = {
    'BLANK_LINE': r'^\s*$',
    'COMMENT_LINE': r'^//.*$',
    'METADATA_LINE': r'^#\s*([^:]+?)\s*:\s*?(.+?)\s*?$',
    'HASH_LINE': r'^#.*$',
    'PSP_START_LINE': r'^Initxx',
}
TOKENS = {k: re.compile(v) for k, v in TOKENS.items()}


METADATA = {
    'MinimalValues': Tuple(float, sep=' '),
    'MaximalValues': Tuple(float, sep=' '),
    'PointNumberPerAxis': Tuple(int),
    'PointSize': int,
    'ColumnDescription': Tuple(str),
}


def parse(io):
    section = 'meta'
    csv_reader = None

    for line in io:
        token, match = None, None

        if section == 'meta':
            for token, pattern in TOKENS.items():
                match = pattern.match(line)
                if match:
                    break
            if not match:
                token = None

            if token in ('BLANK_LINE', 'COMMENT_LINE', 'HASH_LINE'):
                continue

            if token == 'METADATA_LINE':
                key, value = match.group(1), match.group(2)
                yield (section, (key, METADATA.get(key, str)(value)))
            elif token == 'PSP_START_LINE':
                section = 'data'
            elif token is None:
                section = 'data'
                csv_reader = csv.DictReader(io, delimiter=' ')
                break

        elif section == 'data':
            values = SPACES.split(line.strip())
            yield (section, tuple(map(partial(cast, to_type=int), values)))

    if csv_reader:
        for row in csv_reader:
            yield (section, row)


if __name__ == '__main__':
    import sys
    from pathlib import Path
    from pprint import pprint

    if len(sys.argv) < 2:
        print(f"{sys.argv[0]} <file>", file=sys.stderr)
        sys.exit(1)

    f = Path(sys.argv[1])

    if not f.is_file():
        print(f"No such file: {f}", file=sys.stderr)
        sys.exit(1)

    with open(f, newline='') as fp:
        pprint(list(parse(fp)))
