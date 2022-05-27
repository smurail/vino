import json

from django.views.generic import TemplateView, ListView, DetailView
from django.forms.models import model_to_dict
from django.utils.safestring import mark_safe

from vino.kernels.distance import Matrix, EucNorm

from ..models import Kernel, ViabilityProblem, Software, DataFormat
from .json import JsonDetailView


class ModalMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def instance_to_serializable(instance):
            return {
                k: str(v) for k, v in model_to_dict(instance).items()
            }

        def queryset_to_dict(queryset):
            return {
                instance.pk: instance_to_serializable(instance)
                for instance in queryset
            }

        database = mark_safe(json.dumps({
            'software': queryset_to_dict(Software.objects.all()),
            'dataformat': queryset_to_dict(DataFormat.objects.all()),
        }))

        return dict(context, database=database)


class HomeView(ModalMixin, TemplateView):
    template_name = 'sharekernel/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(context, **{
            'last_viabilityproblems': ViabilityProblem.objects.active().with_dimensions().last_updated()[:6],
            'last_kernels': Kernel.objects.active().last_created()[:12],
        })


class ExploreView(ModalMixin, ListView):
    context_object_name = 'viabilityproblems'
    queryset = ViabilityProblem.objects.active().with_dimensions().last_updated()  # type: ignore
    template_name = 'sharekernel/explore.html'


class ViabilityProblemView(ModalMixin, DetailView):
    context_object_name = 'vp'
    queryset = ViabilityProblem.objects.active().with_dimensions()  # type: ignore
    template_name = 'sharekernel/viabilityproblem.html'


class VisualizationDemoView(ListView):
    context_object_name = 'kernels'
    queryset = Kernel.objects.active().all()
    template_name = 'sharekernel/visualization_demo.html'


class KernelData(JsonDetailView):
    model = Kernel

    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        original_format = str(kernel.format)
        ppa = self.kwargs.get('ppa')
        if ppa is not None and ppa > 1:
            debug = False
            bgk = kernel.to_bargrid(ppa=ppa, debug=debug)
            if bgk:
                kernel = kernel if debug else bgk

        distance = self.kwargs.get('distance')
        if distance and ppa is not None:
            borders = [True]*kernel.dimension
            d = Matrix.initFromBarGridKernel(kernel)
            d.distance(EucNorm(), borders, borders)
            distances = d.toData(kernel)
        else:
            distances = None

        return {
            'vp': kernel.vp.id,
            'format': str(kernel.format),
            'originalFormat': original_format,
            'variables': [
                {
                    'name': v.name,
                    'fullname': v.fullname,
                    'data': list(kernel.data_for_axis(i)) if distances is None else list(distances[:, i]),
                }
                for i, v in enumerate(kernel.variables)
            ],
            'rectangles': kernel.rectangles,
            'distances': None if distances is None else list(distances[:, -1])
        }
