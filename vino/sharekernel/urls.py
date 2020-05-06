from django.urls import path, include
from django.conf import settings

from .views import HomeView, VisualizationDemoView, KernelData


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('visualization-demo', VisualizationDemoView.as_view(), name='visualization-demo'),
    path('kernel/<int:pk>/data/', KernelData.as_view(), name='kernel_data'),
]


if settings.DEBUG:
    import debug_toolbar  # type: ignore
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
