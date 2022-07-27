from __future__ import annotations

import contextlib
import pandas as pd

from typing import TextIO
from os import PathLike

from vino import Vino
from vino.typing import AnyPath


def save_csv(file: TextIO | AnyPath, vino: Vino) -> None:
    """Write Vino in RichCSV file format."""

    with contextlib.ExitStack() as stack:
        # Open file if not already done
        # XXX Keep this isinstance to make static type checker happy
        if isinstance(file, (str, bytes, PathLike)):
            # XXX pandas write_csv needs newline=''
            file = stack.enter_context(open(file, 'w', newline=''))

        # Write metadata
        for field in vino.metadata:
            value = vino.metadata.get_unparsed(field)
            file.write(f'#{field}: {value}\n')

        # XXX If number of vino data array dimensions is greater than 2,
        #     we have to flatten it to be able to save it in CSV format.
        #     Vino subclasses are in charge of restoring original shape.
        #     See `RegularGrid` class constructor in `vino.core` module.
        data = vino.ravel().reshape((-1, 1)) if vino.ndim > 2 else vino

        # Write data
        pd.DataFrame(data).to_csv(file, sep=' ', index=False)
