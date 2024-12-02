from django.urls import path, include
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("list/", list),
    path("products/<int:id>", single, name="products-detail"),
    path("categories/", categories),
    path('inventory-report/',inventory_report, name='inventory_report'),
]
# if settings.DEBUG:
#     # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     # if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
