#!/usr/bin/env python
import django

django.setup()

import re
import csv
import numpy as np

from dataclasses import dataclass
from functools import partial, reduce
from itertools import chain
from typing import Tuple, Iterable, Optional, Type, Dict, Any, List, Callable
from collections import OrderedDict
from abc import ABC, abstractmethod


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
    match = DIGITS.search(value).group() # type: ignore
    return cast(match, int)


def compose(*functions):
    def inner(arg):
        return reduce(lambda arg, func: func(arg), functions, arg)
    return inner


class Field(ABC):
    @abstractmethod
    def parse(self, inp: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def unparse(self, value: Any) -> str:
        raise NotImplementedError


class TupleField(Field):
    def __init__(self, typ, sep=','):
        self.type = typ
        self.separator = sep

    def parse(self, inp):
        typ, sep = self.type, self.separator
        tokens = inp.strip().split(sep)
        return [cast(item.strip(), typ) for item in tokens if item.strip()]

    def unparse(self, value):
        return self.separator.join((str(x) for x in value))


class BuiltinTypeField(Field):
    TYPE: Optional[Type] = None

    @classmethod
    def parse(cls, inp):
        return cast(inp, cls.TYPE)

    @classmethod
    def unparse(cls, value):
        return str(value)


class IntegerField(BuiltinTypeField):
    TYPE = int


class StringField(BuiltinTypeField):
    TYPE = str


@dataclass(frozen=True)
class Datum:
    DATA = 'data'
    META = 'meta'

    section: str = DATA
    data: Tuple = ()

    def __init__(self, section: str = section, data: Iterable = data):
        object.__setattr__(self, 'section', section)
        object.__setattr__(self, 'data', tuple(data))


SPACES = re.compile(r' +')
TOKENS = {
    'BLANK_LINE':     re.compile(r'^\s*$'),
    'COMMENT_LINE':   re.compile(r'^//.*$'),
    'METADATA_LINE':  re.compile(r'^#\s*([^:]+?)\s*:\s*?(.+?)\s*?$'),
    'HASH_LINE':      re.compile(r'^#.*$'),
    'PSP_START_LINE': re.compile(r'^Initxx'),
}


class Metadata(dict):
    """
    MinimalValues = TupleField(float, sep=' ')
    MaximalValues = TupleField(float, sep=' ')
    PointNumberPerAxis = TupleField(int)
    PointSize = IntegerField()
    ColumnDescription = TupleField(str)
    dataformat__name = StringField()
    dataformat__columns = TupleField(str)
    """


METADATA: Dict[str, Field] = {
    'MinimalValues': TupleField(float, sep=' '),
    'MaximalValues': TupleField(float, sep=' '),
    'PointNumberPerAxis': TupleField(int),
    'PointSize': IntegerField(),
    'ColumnDescription': TupleField(str),
    'dataformat.name': StringField(),
    'dataformat.columns': TupleField(str),
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
                    yield Datum(Datum.META, ('dataformat.name', 'bars'))
                    section = Datum.DATA

            else:
                yield Datum(Datum.META, ('dataformat.name', 'kdtree'))
                section = Datum.DATA
                csv_reader = csv.DictReader(chain([line], inp), delimiter=' ')
                break

        elif section == Datum.DATA:
            values = SPACES.split(line.strip())
            typed_values = (cast(x, int) for x in values)
            yield Datum(section, typed_values)

    if csv_reader:
        for row in csv_reader:
            typed_values = ((k, cast(v, float)) for k, v in row.items())
            yield Datum(section, typed_values)


def parse_metadata(data: Iterable[Datum]) -> Iterable[Datum]:
    for datum in data:
        if datum.section == Datum.META:
            key, value = datum.data
            if key in METADATA:
                parse = METADATA[key].parse
                yield Datum(datum.section, (key, parse(value)))
        else:
            yield datum


def feed_metadata(data: Iterable[Datum], metadata: Metadata) -> Iterable[Datum]:
    for datum in data:
        if datum.section == Datum.META:
            key, value = datum.data
            metadata[key] = value
        yield datum


def to_vectors(data: Iterable[Datum], metadata: Metadata) -> Iterable[Datum]:
    columns: Tuple[Any, ...] = ()

    for datum in data:
        if datum.section == Datum.DATA:
            dataformat = metadata['dataformat.name']
            values: Iterable[Any]

            if dataformat == 'bars':
                original_columns = metadata['ColumnDescription']
                if not columns:
                    columns = tuple(c for c in original_columns if c != 'empty')
                    metadata['dataformat.columns'] = columns
                data_items = zip(original_columns, datum.data)
                values = (v for k, v in data_items if k != 'empty')

            else:
                data_dict = OrderedDict(datum.data)
                values = data_dict.values()
                if not columns:
                    columns = tuple(data_dict.keys())
                    metadata['dataformat.columns'] = columns

            yield Datum(datum.section, values)

        else:
            yield datum


def normalize_data(data: Iterable[Datum], metadata: Metadata) -> Iterable[Datum]:
    permut_cols = None
    column_indices: List[int] = []
    resample: List[Callable] = []

    for datum in data:
        if datum.section == Datum.DATA and metadata['dataformat.name'] == 'bars':
            # Make permutation matrices
            if permut_cols is None:
                columns = metadata['dataformat.columns']
                assert columns
                count = len(columns)
                # Initialize permutation matrix with zeros
                permut_cols = np.zeros((count, count), int)
                permut_axes = np.zeros((count-1, count-1), int)
                # Find column indices out of column labels (x1, x2...)
                column_indices = [to_int(c)-1 for c in columns]
                # Two last columns are bounds of a bar
                assert column_indices[-1] == column_indices[-2]
                bar_axis = column_indices[-1]
                permut_fields_vector = column_indices[:-1]
                # Shift all columns after max bound (ie. xNmax)
                permut_vector = [x+1 if x > bar_axis else x for x in column_indices]
                permut_vector[-1] += 1
                # Make permutation matrices out of permutation vector
                for i in range(len(permut_vector)):
                    permut_cols[permut_vector[i]][i] = 1
                for i in range(len(permut_fields_vector)):
                    permut_axes[permut_fields_vector[i]][i] = 1
                # Permute column labels by permuting column indices
                columns = [columns[i] for i in np.dot(permut_cols, range(count))]
                metadata['dataformat.columns'] = columns

            # Make resampling functions
            if not resample:
                min_values = np.dot(permut_axes, metadata['MinimalValues'])
                max_values = np.dot(permut_axes, metadata['MaximalValues'])
                ppa_values = np.dot(permut_axes, metadata['PointNumberPerAxis'])
                assert len(min_values) == len(max_values) == len(ppa_values)
                resampling_values = list(zip(min_values, max_values, ppa_values))
                for i in column_indices:
                    vmin, vmax, ppa = resampling_values[i]
                    resample.append(lambda x: vmin + x/ppa * (vmax-vmin))

            # Compute results
            resampled = [resample[i](x) for i, x in enumerate(datum.data)]
            permuted = np.dot(permut_cols, resampled)
            normalized = permuted

            yield Datum(datum.section, normalized)

        else:
            yield datum


def to_dicts(data: Iterable[Datum], metadata: Metadata) -> Iterable[Datum]:
    yielded_metadata = False

    for datum in data:
        if datum.section == Datum.DATA:
            if not yielded_metadata:
                for item in metadata.items():
                    yield Datum(Datum.META, item)
                yielded_metadata = True

            columns = metadata['dataformat.columns']
            assert len(columns) == len(datum.data)
            values = ((k, v) for k, v in zip(columns, datum.data))
            yield Datum(datum.section, values)


def write_csv(data: Iterable[Datum], target: str, metadata: Metadata) -> Iterable[Datum]:
    with open(target, 'w') as out:
        writer = None

        for datum in data:
            if datum.section == Datum.META:
                key, value = datum.data
                unparse = METADATA[key].unparse or str
                out.write(f'#{key}: {unparse(value)}\n')

            elif datum.section == Datum.DATA:
                if not writer:
                    fields = OrderedDict(datum.data).keys()
                    writer = csv.DictWriter(out, fieldnames=fields, delimiter=' ')
                    writer.writeheader()
                writer.writerow(OrderedDict(datum.data))

            yield datum


def parse(inp: Iterable[str]) -> Iterable[Datum]:
    metadata = Metadata({})
    pipeline = compose(
        parse_datafile,
        parse_metadata,
        partial(feed_metadata, metadata=metadata),
        partial(to_vectors, metadata=metadata),
        partial(normalize_data, metadata=metadata),
        partial(to_dicts, metadata=metadata),
        partial(write_csv, target='data/data.csv', metadata=metadata),
    )

    return pipeline(inp)


if __name__ == '__main__':
    import sys
    from pathlib import Path
    # XXX https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python/30091579#30091579
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE, SIG_DFL)

    if len(sys.argv) < 2:
        print(f"{sys.argv[0]} <file>", file=sys.stderr)
        sys.exit(1)

    f = Path(sys.argv[1])

    if not f.is_file():
        print(f"No such file: {f}", file=sys.stderr)
        sys.exit(1)

    with open(f, newline='') as fp:
        for r in parse(fp):
            print(r)
