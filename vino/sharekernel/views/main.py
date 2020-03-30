from django.views.generic import TemplateView

from ..models import Kernel, Symbol
from .json import JsonDetailView


class HomeView(TemplateView):
    template_name = 'sharekernel/home.html'


class VisualizeView(TemplateView):
    template_name = 'sharekernel/visualize.html'


class KernelData(JsonDetailView):
    model = Kernel

    def get_context_data(self, **kwargs):
        kernel = self.get_object()
        variables = [v.fullname for v in kernel.vp.state_variables]
        return {
            'base': 0,
            'x': [values[1] for values in kernel.data],
            'y': [values[2] for values in kernel.data],
            'xtitle': variables[0],
            'ytitle': variables[1],
        }
