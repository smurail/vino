from __future__ import annotations

import pytest
import numpy as np

from typing import NamedTuple
from pathlib import Path

import vino as vn


SAMPLES_PATH = "samples"


class Expect(NamedTuple):
    cls: type[vn.Vino] | None = None
    dtype: npt.DTypeLike | None = None
    count: int | None = None
    first: list[int | float] | None = None
    last: list[int | float] | None = None


samples = [
    pytest.param(
        ("lake", "2D.txt", "2D_metadata.txt"),
        Expect(
            cls=vn.BarGrid,
            dtype=np.uint32,
            count=65537,
            first=[0, 0, 53241],
            last=[65536, 0, 6183],
        ),
        id="lake_psp"
    ),
    pytest.param(
        ("lake", "2D_light.txt", "2D_light_metadata.txt"),
        Expect(
            cls=vn.BarGrid,
            dtype=np.uint32,
            count=16385,
            first=[0, 0, 53400],
            last=[65536, 0, 6288],
        ),
        id="lake_psp_light"
    ),
    pytest.param(
        ("lake", "lake_Isa_R1.dat", "lake_Isa_R1.txt"),
        Expect(
            cls=vn.KdTree,
            dtype=np.float64,
            count=6335,
            first=[0.10043945312500001, 6.8359375e-4, 0.1, 0.10087890625000001, 0.0, 0.0013671875, 3.469446951953614e-18],
            last=[0.671728515625, 0.70205078125, 0.6712890625000001, 0.6721679687500001, 0.7013671874999999, 0.7027343749999999, -0.09],
        ),
        id="lake_viabilitree"
    ),
    pytest.param(
        ("bilingual-viabilitree", "bilingual21dil0control0.1ustep0.01WC.dat", "bilingual21dil0control0.1ustep0.01WC.txt"),
        Expect(
            cls=vn.KdTree,
            dtype=np.float64,
            count=43259
        ),
        id="bilingual_viabilitree"
    ),
    pytest.param(
        ("bilingual-viabilitree", "Bilingual21TS05dil3.dat", "Bilingual21TS05dil3.txt"),
        Expect(
            cls=vn.KdTree,
            dtype=np.float64,
            count=50763
        ),
        id="bilingual_viabilitree_dil3"
    ),
    pytest.param(
        ("rangeland", "3D_rangeland.txt", "3D_rangeland_metadata.txt"),
        Expect(
            vn.BarGrid,
            dtype=np.uint32,
            count=292379,
        ),
        id="rangeland"
    ),
    pytest.param(
        ("4d", "4d_cylinder_data.txt", "4d_cylinder_metadata.txt"),
        Expect(
            cls=vn.BarGrid,
            dtype=np.uint32,
            count=17430,
        ),
        id="4d_cylinder"
    ),
    pytest.param(
        ("4d", "lake4D16.dat", "lake4D16.txt"),
        Expect(
            cls=vn.KdTree,
            dtype=np.float64,
            count=25552,
        ),
        id="4d_lake"
    ),
    pytest.param(
        ("polygon", "lake_polygon.dat", "lake_polygon_metadata.txt"),
        Expect(
            cls=vn.Polygon,
            dtype=np.float64,
            count=721,
        ),
        id="lake_polygon"
    ),
    pytest.param(
        ("polygon", "LV.dat", "LV_metadata.txt"),
        Expect(
            cls=vn.Polygon,
            dtype=np.float64,
            count=213,
        ),
        id="LV"
    ),
]


@pytest.mark.parametrize("location, expect", samples)
def test_load(location, expect):
    path, *files = location
    sources = [Path(SAMPLES_PATH) / path / f for f in files]
    vino = vn.load(*sources)

    assert isinstance(vino, vn.Vino)
    assert expect.cls   is None or isinstance(vino, expect.cls)
    assert expect.dtype is None or vino.dtype == expect.dtype
    assert expect.count is None or len(vino) == expect.count
    assert expect.first is None or np.all(vino[0] == expect.first)
    assert expect.last  is None or np.all(vino[-1] == expect.last)
