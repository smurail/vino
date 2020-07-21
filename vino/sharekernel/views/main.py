from django.views.generic import TemplateView, DetailView

from ..models import Kernel, BarGridKernel, KdTreeKernel, ViabilityProblem
from .json import JsonDetailView


class HomeView(TemplateView):
    template_name = 'sharekernel/home.html'

    def get_context_data(self, **kwargs):
        return {
            'last_viabilityproblems': ViabilityProblem.objects.active().with_dimensions().last_updated()[:6],
            'last_kernels': Kernel.objects.active().last_created()[:12],
        }


class ViabilityProblemView(DetailView):
    context_object_name = 'vp'
    queryset = ViabilityProblem.objects.active().with_dimensions()  # type: ignore
    template_name = 'sharekernel/viabilityproblem.html'


class VisualizationDemoView(TemplateView):
    template_name = 'sharekernel/visualization_demo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kernels = Kernel.objects.active().filter(size__lt=100000).all()
        context['kernels'] = [
            (k.pk, f"{k.params.vp}: {k.title} ({k.size})") for k in kernels
        ]
        return context


class KernelData(JsonDetailView):
    model = Kernel

    def get_context_data(self, **kwargs):
        kernel = self.get_object()

        original_format = kernel.format.title
        if kernel.dimension == 2 and isinstance(kernel, KdTreeKernel):
            ppa = self.kwargs.get('ppa')
            if ppa is not None:
                debug = False
                bgk = kernel.to_bargrid(ppa=ppa, debug=debug)
                assert isinstance(bgk, BarGridKernel)
                original_format = kernel.format.title
                kernel = kernel if debug else bgk

        return {
            'vp': kernel.vp.id,
            'format': kernel.format.title,
            'originalFormat': original_format,
            'variables': [
                {
                    'name': v.name,
                    'fullname': v.fullname,
                    'data': list(kernel.data_for_axis(i)),
                }
                for i, v in enumerate(kernel.variables)
            ],
            'rectangles': kernel.rectangles,
        }
