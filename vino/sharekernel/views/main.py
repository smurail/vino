import json

from django.views.generic import TemplateView, ListView, DetailView
from django.forms.models import model_to_dict
from django.utils.safestring import mark_safe

from ..models import Kernel, ViabilityProblem, Software, DataFormat


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
