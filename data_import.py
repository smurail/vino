#!/usr/bin/env python
import django

django.setup()

import re
import csv

from dataclasses import dataclass
from functools import partial, reduce
from itertools import chain
from typing import Tuple, Iterable, Dict, Any, Optional, NewType


Metadata = NewType('Metadata', Dict[str, Any])


NO_DEFAULT = object()


def cast(value, to_type, default=NO_DEFAULT):
    try:
        if type(value) is to_type:
            return value
        return to_type(value)
    except ValueError:
        return to_type() if default is NO_DEFAULT else default


def compose(*functions):
    def inner(arg):
        return reduce(lambda arg, func: func(arg), functions, arg)
    return inner


def TupleField(typ, sep=','):
    def parser(inp):
        return [cast(item.strip(), typ) for item in inp.split(sep)]
    return parser


@dataclass(frozen=True)
class Datum:
    DATA = 'data'
    META = 'meta'

    section: str = DATA
    data: Tuple = ()


SPACES = re.compile(r' +')
TOKENS = {
    'BLANK_LINE':     re.compile(r'^\s*$'),
    'COMMENT_LINE':   re.compile(r'^//.*$'),
    'METADATA_LINE':  re.compile(r'^#\s*([^:]+?)\s*:\s*?(.+?)\s*?$'),
    'HASH_LINE':      re.compile(r'^#.*$'),
    'PSP_START_LINE': re.compile(r'^Initxx'),
}


METADATA = {
    'MinimalValues': TupleField(float, sep=' '),
    'MaximalValues': TupleField(float, sep=' '),
    'PointNumberPerAxis': TupleField(int),
    'PointSize': int,
    'ColumnDescription': TupleField(str),
}


def parse_datafile(inp: Iterable[str]) -> Iterable[Datum]:
    section = Datum.META
    csv_reader = None

    for line in inp:
        token = None

        if section == Datum.META:
            for token, pattern in TOKENS.items():
                match = pattern.match(line)
                if match:
                    break

            if match:
                if token in ('BLANK_LINE', 'COMMENT_LINE', 'HASH_LINE'):
                    continue

                elif token == 'METADATA_LINE':
                    key, value = match.group(1), match.group(2)
                    yield Datum(section, (key, value))

                elif token == 'PSP_START_LINE':
                    section = Datum.DATA

            else:
                section = Datum.DATA
                csv_reader = csv.DictReader(chain([line], inp), delimiter=' ')
                break

        elif section == Datum.DATA:
            values = SPACES.split(line.strip())
            typed_values = tuple(cast(x, int) for x in values)
            yield Datum(section, typed_values)

    if csv_reader:
        for row in csv_reader:
            typed_values = tuple((k, cast(v, float)) for k, v in row.items())
            yield Datum(section, typed_values)


def parse_metadata(data: Iterable[Datum]) -> Iterable[Datum]:
    for datum in data:
        if datum.section == Datum.META:
            key, value = datum.data
            parse_value = METADATA.get(key) or str
            yield Datum(datum.section, (key, parse_value(value)))
        else:
            yield datum


def feed_metadata(data: Iterable[Datum], metadata: Optional[Metadata] = None) -> Iterable[Datum]:
    for datum in data:
        if datum.section == Datum.META:
            key, value = datum.data
            if metadata:
                metadata[key] = value
        yield datum


def parse_data(data: Iterable[Datum], metadata: Optional[Metadata] = None) -> Iterable[Datum]:
    for datum in data:
        if datum.section == Datum.DATA:
            columns = metadata and metadata.get('ColumnDescription')
            if columns:
                values = ((k, v) for k, v in zip(columns, datum.data) if k != 'empty')
                yield Datum(datum.section, tuple(values))
                continue
        yield datum


def parse(inp: Iterable[str]) -> Iterable[Datum]:
    metadata = Metadata({})
    pipeline = compose(
        parse_datafile,
        parse_metadata,
        partial(feed_metadata, metadata=metadata),
        partial(parse_data, metadata=metadata))

    return pipeline(inp)


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
