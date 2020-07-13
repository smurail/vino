from django.views.generic import TemplateView

from ..models import Kernel
from .json import JsonDetailView


class HomeView(TemplateView):
    template_name = 'sharekernel/home.html'


class VisualizationDemoView(TemplateView):
    template_name = 'sharekernel/visualization_demo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kernels = Kernel.objects.filter(size__lt=100000).all()
        context['kernels'] = [
            (k.pk, f"{k.params.vp}: {k.title} ({k.size})") for k in kernels
        ]
        return context


class KernelData(JsonDetailView):
    model = Kernel

    def get_context_data(self, **kwargs):
        kernel = self.get_object()
        return {
            'vp': kernel.vp.id,
            'format': kernel.format.title,
            'variables': [
                {
                    'name': v.name,
                    'fullname': v.fullname,
                    'data': list(kernel.data_for_axis(i)),
                }
                for i, v in enumerate(kernel.variables)
            ],
            'shapes': kernel.shapes,
        }
