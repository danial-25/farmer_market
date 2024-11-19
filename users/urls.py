from django.urls import path
from .views import *

urlpatterns = [
    path("register/farmer/", FarmerRegistrationView.as_view(), name="register_farmer"),
    path("register/buyer/", BuyerRegistrationView.as_view(), name="register_buyer"),
    path("login/", user_login, name="login_buyer"),
]
