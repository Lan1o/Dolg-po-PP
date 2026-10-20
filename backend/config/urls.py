from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


def health(request):
    """Простой health-check для проверки, что API живо."""
    return JsonResponse({
        'status': 'ok',
        'service': 'CampusThesis API',
        'version': '0.1.0',
    })


urlpatterns = [
    path('admin/', admin.site.urls),

    # health
    path('api/health', health, name='health'),

    # swagger / openapi
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# В DEBUG отдаём media-файлы через Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)