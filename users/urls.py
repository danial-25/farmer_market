from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register('farmers', FarmerViewSet, basename='farmer')

urlpatterns = [
    path("register/farmer/", FarmerRegistrationView.as_view(), name="register_farmer"),
    path("register/buyer/", BuyerRegistrationView.as_view(), name="register_buyer"),
    path("login/", user_login, name="login_buyer"),
    path("farmers/", list_farmers),
    path("farmer/<int:id>", FarmerUpdateAPIView.as_view(), name="farmer"),
    #   path("farmer/<int:id>", FarmerEditView.as_view(), name="farmer"),
    # path(
    #     "farmer/delete/<int:id>/", FarmerDeleteAPIView.as_view(), name="farmer-delete"),
    path("buyers/", list_buyers, name="list_buyers"),  # List all buyers
    path("buyers/<int:id>/", BuyerUpdateAPIView.as_view(), name="buyer_update"),
    path(
        "admin/pending-farmers/",
        PendingFarmersAPIView.as_view(),
        name="pending-farmers",
    ),
    # You can also add a path for approving/rejecting a specific farmer
    path(
        "admin/pending-farmers/<int:id>/",
        PendingFarmersAPIView.as_view(),
        name="approve-reject-farmer",
    ),
    path("buyers/cart/", views.get_cart, name="get_cart"),
    path("buyers/cart/add/", views.add_to_cart, name="add_to_cart"),
    path("buyers/cart/apply-promo/", views.apply_promo_code, name="apply_promo_code"),
]
