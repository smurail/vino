from django.views.generic import TemplateView

from ..models import Kernel, BarGridKernel, KdTreeKernel
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
        state_variables = kernel.vp.state_variables
        dim = len(state_variables)
        offset = 1 if isinstance(kernel, BarGridKernel) else 0
        data = {
            'x': [values[offset] for values in kernel.data],
            'y': [values[offset+1] for values in kernel.data],
            'variables': [
                {
                    'name': v.name,
                    'fullname': v.fullname
                }
                for v in state_variables
            ]
        }
        if isinstance(kernel, KdTreeKernel):
            data['rectangles'] = [
                values[dim:3*dim] for values in kernel.data
            ]
        if dim > 2:
            data['z'] = [values[offset+2] for values in kernel.data]
        return data
