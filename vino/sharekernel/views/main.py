from django.views.generic import TemplateView

from ..models import Kernel
from .json import JsonDetailView


class HomeView(TemplateView):
    template_name = 'sharekernel/home.html'


class VisualizationDemoView(TemplateView):
    template_name = 'sharekernel/visualization-demo.html'

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
        variables = [v.fullname for v in kernel.vp.state_variables]
        offset = 1 if kernel.format.title == 'bars' else 0
        data = {
            'x': [values[offset] for values in kernel.data],
            'y': [values[offset+1] for values in kernel.data],
            'xtitle': variables[0],
            'ytitle': variables[1],
        }
        if len(variables) > 2:
            data['z'] = [values[offset+2] for values in kernel.data]
            data['ztitle'] = variables[2]
        return data
