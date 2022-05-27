import numpy as np
import vino as vn

from ..models import Kernel
from .json import JsonDetailView


def vino_from_kernel(kernel=None):
    files = [sf.file for sf in kernel.sourcefiles.all()]
    return vn.load(*files)


def axes_from_vino(vno):
    ranges = vno.bounds.T.tolist()
    return [
        {
            'order': v.order,
            'axis': v.axis,
            'name': v.name,
            'desc': v.desc,
            'unit': v.unit,
            'range': ranges[v.order],
        } for v in vno.variables
    ]


def info_from_vino(kernel, vno, original=None, axes_subset=None):
    assert axes_subset is None or len(axes_subset) <= vno.dim

    dim = vno.dim if axes_subset is None else len(axes_subset)
    axes = axes_from_vino(vno)
    info = {
        'id': kernel.id,
        'vp': kernel.vp.id,
        'title': kernel.title,
        'dim': dim,
        'format': vno.DATAFORMAT,
        'size': len(vno),
        'axes': axes if axes_subset is None else [axes[a] for a in axes_subset],
    }

    if original is not None:
        info.update(
            format=vno.DATAFORMAT,
            size=vno.size,
            original=dict(format=original.DATAFORMAT, size=original.size),
        )

    if isinstance(vno, vn.RegularGrid):
        if axes_subset is None:
            ppa, origin, opposite = vno.ppa, vno.origin, vno.opposite
            unit, bounds = vno.unit, vno.bounds
        else:
            a = list(axes_subset)
            ppa = vno.ppa[a]
            origin = vno.origin[a]
            opposite = vno.opposite[a]
            unit = vno.unit[a]
            bounds = np.ascontiguousarray(vno.bounds.T[a].T)
        info.update(
            grid=dict(
                ppa=ppa,
                origin=origin,
                opposite=opposite,
                unit=unit,
                bounds=bounds))

    return info


def error(msg):
    return {
        "error": msg
    }


class VinoDetailView(JsonDetailView):
    model = Kernel

    def get_ppa(self):
        ppa = self.kwargs.get('ppa')
        return None if not ppa else ppa[0] if len(ppa) == 1 else ppa


class VinoData(VinoDetailView):
    info_only = False
    format = None

    def get_context_data(self, **kwargs):
        kernel = self.get_object()
        vno = vino_from_kernel(kernel)
        original = None

        if not self.info_only and vno.dim > 3:
            return error(
                f"Can't visualize {vno.dim}-dimensional vino, use sections")

        ppa = self.get_ppa()
        if ppa is not None:
            original = vno

            if self.format == 'regulargrid':
                vno = vno.to_regulargrid(ppa=ppa)
            else:
                vno = vno.to_bargrid(ppa=ppa)

        info = info_from_vino(kernel, vno, original)
        if self.info_only:
            return info

        if vno.dim == 3 and isinstance(vno, vn.BarGrid):
            vno = vno.hull()

        data = vno.points_coordinates()

        return dict(info, values=[
            np.ascontiguousarray(data[:, v.order]) for v in vno.variables
        ])


class VinoShapes(VinoDetailView):
    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        if kernel.dimension != 2:
            return error("Only 2-dimensional vinos have shapes")

        vno = vino_from_kernel(kernel)
        original = None

        ppa = self.get_ppa()
        if ppa is not None:
            original = vno
            vno = vno.to_bargrid(ppa=ppa)

        rectangles = vno.rectangles_coordinates()

        return dict(info_from_vino(kernel, vno, original), shapes=[
            rectangles[0], rectangles[1],
        ])


class VinoSection(VinoDetailView):
    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        dim = kernel.dimension
        if dim < 3:
            return error(f"Can't make sections from a {dim}-dimensional vino")

        ppa = self.get_ppa()
        plane = self.kwargs.get('plane')
        at = self.kwargs.get('at')

        if len(plane) != 2:
            return error("Please provide 2 axes to define the cutting plane")

        original = vino_from_kernel(kernel)
        vno = original.to_regulargrid(ppa=ppa or -1)
        info = info_from_vino(kernel, vno, original, plane)
        axes = info['axes']

        m = vno.dim - len(plane)
        if len(at) != m:
            return error(
                f"Please provide {m} ax{'i' if m == 1 else 'e'}s to specify section position")

        section = vno.section(plane, at)

        return dict(info, values=[
            np.ascontiguousarray(section[:, a]) for a in range(len(plane))
        ])
