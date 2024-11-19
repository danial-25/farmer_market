from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('farmers', FarmerViewSet, basename='farmer')

urlpatterns = [
    path("register/farmer/", FarmerRegistrationView.as_view(), name="register_farmer"),
    path("register/buyer/", BuyerRegistrationView.as_view(), name="register_buyer"),
    path("login/", user_login, name="login_buyer"),
    path('', include(router.urls))
]
