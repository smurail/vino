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

        # Write data
        pd.DataFrame(vino).to_csv(file, sep=' ', index=False)
