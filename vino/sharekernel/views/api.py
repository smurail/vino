import numpy as np
import vino as vn

from ..models import Kernel
from .json import JsonDetailView


def info_from_vino(kernel, vno, original=None, axes=None):
    dim = vno.dim
    ranges = vno.bounds.T.tolist()
    info = dict(
        id=kernel.id,
        vp=kernel.vp.id,
        title=kernel.title,
        dim=dim,
        format=vno.DATAFORMAT,
        size=len(vno),
        axes=axes or list(range(dim)),
        variables=[
            dict(
                order=v.order,
                axis=v.axis,
                name=v.name,
                desc=v.desc,
                unit=v.unit,
                range=ranges[v.order],
            ) for v in vno.variables
        ]
    )

    if original is not None:
        info['original'] = dict(
            format=original.DATAFORMAT,
            size=len(original),
        )

    if isinstance(vno, vn.RegularGrid):
        info['grid'] = dict(
            ppa=vno.ppa,
            origin=vno.origin,
            opposite=vno.opposite,
            unit=vno.unit,
            bounds=vno.bounds,
        )

    return info


def error(msg):
    return {
        "error": msg
    }


class VinoDetailView(JsonDetailView):
    model = Kernel

    def get_ppa(self):
        ppa = self.kwargs.get('ppa')

        if ppa is None:
            return None

        if all(x <= 0 for x in ppa):
            return -1

        return ppa[0] if len(ppa) == 1 else ppa

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.ppa = self.get_ppa()


class VinoData(VinoDetailView):
    info_only = False
    format = None
    weight = None

    def get_context_data(self, **kwargs):
        kernel = self.get_object()
        vno = kernel.data
        original = None

        if not self.info_only and vno.dim > 3:
            return error(
                f"Can't visualize {vno.dim}-dimensional vino, use sections")

        if self.ppa is not None:
            original = vno

            if self.format == 'regulargrid':
                vno = vno.to_regulargrid(ppa=self.ppa)
            else:
                vno = vno.to_bargrid(ppa=self.ppa)

        info = info_from_vino(kernel, vno, original)
        if self.info_only:
            return info

        if vno.dim == 3 and isinstance(vno, vn.BarGrid):
            vno = vno.hull()

        data = vno.points_coordinates()

        if type(vno) is vn.RegularGrid and self.weight == 'distance':
            info['distances'] = dict(
                values=vno.distances(),
            )

        return dict(info, values=[
            np.ascontiguousarray(data[:, v.order]) for v in vno.variables
        ])


class VinoShapes(VinoDetailView):
    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        if kernel.dimension != 2:
            return error("Only 2-dimensional vinos have shapes")

        vno = kernel.data
        original = None

        if self.ppa is not None:
            original = vno
            vno = vno.to_bargrid(ppa=self.ppa)

        info = info_from_vino(kernel, vno, original)
        rectangles = vno.rectangles_coordinates()

        return dict(info, shapes=[
            rectangles[0], rectangles[1],
        ])


class VinoSection(VinoDetailView):
    weight = None

    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        dim = kernel.dimension
        if dim < 3:
            return error(f"Can't make sections from a {dim}-dimensional vino")

        plane = self.kwargs.get('plane')
        at = self.kwargs.get('at')

        if len(plane) != 2:
            return error("Please provide 2 axes to define the cutting plane")

        m = dim - len(plane)
        if len(at) != m:
            return error(
                f"Please provide {m} ax{'i' if m == 1 else 'e'}s to specify section position")

        for a in plane:
            if a not in range(dim):
                return error(f"Cutting plane axes must be between 0 and {dim-1}")

        original = kernel.data
        vno = original.to_regulargrid(ppa=self.ppa)
        info = info_from_vino(kernel, vno, original, plane)

        if self.weight == 'distance':
            vno = vno.with_distance()

        section = vno.section(plane, at).ravel()
        mask = section if self.weight is None else (section > 0)
        coordinates = vno.grid_coordinates(plane)
        points = coordinates[mask]

        if self.weight == 'distance':
            info['distances'] = dict(
                range=[np.min(vno.ravel()).item(), np.max(vno.ravel()).item()],
                values=np.asarray(section[mask]),
            )

        return dict(info, values=[
            np.ascontiguousarray(points[:, a]) for a in range(len(plane))
        ])
