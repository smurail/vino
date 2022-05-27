from django.urls import path, include, register_converter
from django.conf import settings
from django.views.generic import TemplateView

from .converters import IntTupleConverter
from .views import (HomeView, ExploreView, ViabilityProblemView,
                    VisualizationDemoView, KernelData, VinoData, VinoShapes)


register_converter(IntTupleConverter, 'ints')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('explore', ExploreView.as_view(), name='explore'),
    path('viabilityproblem/<int:pk>/', ViabilityProblemView.as_view(), name='viabilityproblem'),
    path('visualization-demo', VisualizationDemoView.as_view(), name='visualization_demo'),
    path('about', TemplateView.as_view(template_name='sharekernel/about.html'), name='about'),
    path('kernel/<int:pk>/data/', KernelData.as_view(), name='kernel_data'),
    path('kernel/<int:pk>/data/<int:ppa>/', KernelData.as_view()),
    path('kernel/<int:pk>/data/<int:ppa>/distance/', KernelData.as_view(), {'distance': True}),

    # Original vino
    path('api/vino/<int:pk>/', VinoData.as_view(), name='vino_data'),
    path('api/vino/<int:pk>/info/', VinoData.as_view(info_only=True), name='vino_data'),

    # Coerced vino
    path('api/vino/<int:pk>/bargrid/<ints:ppa>/', VinoData.as_view(format='bargrid'), name='vino_data'),
    path('api/vino/<int:pk>/regulargrid/<ints:ppa>/', VinoData.as_view(format='regulargrid'), name='vino_data'),

    # Shapes of a vino
    path('api/vino/<int:pk>/shapes/', VinoShapes.as_view(), name='vino_shapes'),
    path('api/vino/<int:pk>/bargrid/<ints:ppa>/shapes/', VinoShapes.as_view(), name='vino_shapes'),
]


if settings.DEBUG:
    import debug_toolbar  # type: ignore
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
