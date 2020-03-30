from django.urls import path, include
from django.conf import settings

from .views import HomeView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
