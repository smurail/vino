from django.views.generic import TemplateView

from ..models import Kernel
from .json import JsonDetailView


class HomeView(TemplateView):
    template_name = 'sharekernel/home.html'


class VisualizeView(TemplateView):
    template_name = 'sharekernel/visualize.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kernels = Kernel.objects.all()
        context['kernels'] = [
            (k.pk, f"{k.params.vp}: {k.title} ({k.size})") for k in kernels
        ]
        return context


class KernelData(JsonDetailView):
    model = Kernel

    def get_context_data(self, **kwargs):
        kernel = self.get_object()
        variables = [v.fullname for v in kernel.vp.state_variables]
        data = {
            'x': [values[1] for values in kernel.data],
            'y': [values[2] for values in kernel.data],
            'xtitle': variables[0],
            'ytitle': variables[1],
        }
        if len(variables) > 2:
            data['z'] = [values[3] for values in kernel.data]
            data['ztitle'] = variables[2]
        return data
