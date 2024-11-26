from django.urls import path, include
from .views import *
from . import views
from users.views import *

urlpatterns = [
    path("products/create/", views.create_product, name="product-create"),
    path("dashboard/", farmer_dashboard, name="farmer_dashboard"),
    path(
        "products/<int:product_id>/out_of_stock/",
        views.mark_out_of_stock,
        name="mark_out_of_stock",
    ),
    path(
        "products/<int:product_id>/remove/", views.remove_product, name="remove_product"
    ),
    # path(
    #     "product/<int:product_id>/update/", views.update_product, name="update_product"
    # ),
    # "path('product/<slug:product_id>/update/', views.update_product, name='update_product')"
    path(
        "product/<slug:product_id>/update/", views.update_product, name="update_product"
    ),
    path(
        "product/<slug:product_id>/delete/", views.delete_product, name="delete_product"
    ),
    path("profile/", FarmerProfile.as_view()),
    path("farm/", FarmManagementView.as_view()),
]
