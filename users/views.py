from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import *
from products.serializers import *
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny


# Create your views here.
class BuyerRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BuyerSerializer(data=request.data)
        if serializer.is_valid():
            buyer = serializer.save()
            buyer.user.save()
            return Response(
                {"message": "Buyer registered successfully."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FarmerRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FarmerSerializer(data=request.data)
        if serializer.is_valid():
            farmer = serializer.save()
            farmer.user.save()
            return Response(
                {"message": "Farmer registered successfully. Awaiting admin approval."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(["POST"])
# @permission_classes([AllowAny])
# def user_login(request):
#     username = request.data.get("username")
#     password = request.data.get("password")
#     print(username, password)
#     user = authenticate(request, username=username, password=password)
#     if user:
#         token, _ = Token.objects.get_or_create(user=user)
#         return Response({"token": token.key}, status=200)
#     return Response({"error": "Invalid credentials"}, status=401)


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    print(username, password)
    user = authenticate(request, username=username, password=password)

    if user:
        # Check if the user has a Farmer or Buyer profile
        token, _ = Token.objects.get_or_create(user=user)

        # Check the user's role
        if hasattr(user, "farmer_profile"):
            # User is a farmer
            farmer = user.farmer_profile
            if not farmer.is_approved:
                return Response(
                    {"error": "Farmer account is not approved yet."}, status=403
                )
            return Response({"token": token.key, "role": "farmer"}, status=200)

        elif hasattr(user, "buyer_profile"):
            # User is a buyer
            return Response({"token": token.key, "role": "buyer"}, status=200)

        else:
            return Response({"error": "User does not have a valid role."}, status=400)

    return Response({"error": "Invalid credentials"}, status=401)
