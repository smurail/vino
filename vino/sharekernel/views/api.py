import numpy as np
import vino as vn

from ..models import Kernel
from .json import JsonDetailView


def vino_from_kernel(kernel=None):
    files = [sf.file for sf in kernel.sourcefiles.all()]
    return vn.load(*files)


def axes_from_vino(vno):
    ranges = vno.bounds.T.tolist()
    return {
        v.axis: {
            'order': v.order,
            'name': v.name,
            'desc': v.desc,
            'unit': v.unit,
            'range': ranges[v.order],
        } for v in vno.variables
    }


def info_from_vino(kernel, vno):
    return {
        'id': kernel.id,
        'vp': kernel.vp.id,
        'title': kernel.title,
        'dim': vno.dim,
        'format': vno.DATAFORMAT,
        'size': len(vno),
        'axes': axes_from_vino(vno),
    }


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

        assert vno.dim <= 3

        info = info_from_vino(kernel, vno)

        ppa = self.get_ppa()
        if ppa is not None:
            original = vno

            if self.format == 'regulargrid':
                vno = vno.to_regulargrid(ppa=ppa)
            else:
                vno = vno.to_bargrid(ppa=ppa)

            info.update(
                format=vno.DATAFORMAT,
                size=vno.size,
                original=dict(format=original.DATAFORMAT, size=original.size),
            )

        if isinstance(vno, vn.RegularGrid):
            info.update(
                grid=dict(
                    ppa=vno.ppa,
                    origin=vno.origin,
                    opposite=vno.opposite,
                    unit=vno.unit,
                    bounds=vno.bounds))

        if self.info_only:
            return info

        if vno.dim == 3 and isinstance(vno, vn.BarGrid):
            vno = vno.hull()

        data = vno.points_coordinates()

        return dict(info, values={
            v.axis: np.ascontiguousarray(data[:, v.order])
            for v in vno.variables
        })


class VinoShapes(VinoDetailView):
    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        if kernel.dimension != 2:
            return error("Only 2-dimensional vinos have shapes")

        vno = vino_from_kernel(kernel)

        ppa = self.get_ppa()
        if ppa is not None:
            vno = vno.to_bargrid(ppa=ppa)

        rectangles = vno.rectangles_coordinates()

        return dict(info_from_vino(kernel, vno), shapes={
            "x": rectangles[0],
            "y": rectangles[1],
        })
