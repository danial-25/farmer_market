from django.urls import path, include
from .views import *

urlpatterns = [
    path("list/", list),
    path("products/<int:id>", single, name="products-detail"),
]
