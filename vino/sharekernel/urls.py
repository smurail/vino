from django.urls import path, include
from django.conf import settings

from .views import HomeView, VisualizeView, KernelData


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('visualize', VisualizeView.as_view(), name='visualize'),
    path('kernel/<int:pk>/data/', KernelData.as_view(), name='kernel_data'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
