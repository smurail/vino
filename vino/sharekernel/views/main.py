from django.views.generic import TemplateView

from ..models import Kernel
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
        data = {
            'type': 'scattergl',
            'mode': 'markers',
            'x': [values[1] for values in kernel.data],
            'y': [values[2] for values in kernel.data],
            'xtitle': variables[0],
            'ytitle': variables[1],
        }
        if len(variables) > 2:
            data['type'] = 'scatter3d'
            data['z'] = [values[3] for values in kernel.data]
            data['ztitle'] = variables[2]
        return data
