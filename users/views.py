from django.shortcuts import render, get_object_or_404
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
from rest_framework.permissions import IsAdminUser

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.core.mail import send_mail
from .models import Farmer
from .serializers import FarmerSerializer

class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_farmer(self, request, pk=None):
        farmer = self.get_object()
        if farmer.is_approved:
            return Response({"detail": "Farmer is already approved."}, status=status.HTTP_400_BAD_REQUEST)

        farmer.is_approved = True
        farmer.save()

        # Send confirmation email to farmer
        send_mail(
            subject="Your Farmer Account Has Been Approved",
            message=f"Dear {farmer.farm_name},\n\nYour farmer account has been approved. You can now list products on our platform.",
            from_email="admin@example.com",
            recipient_list=[farmer.user.email],
        )

        return Response({"detail": "Farmer approved and notified via email."}, status=status.HTTP_200_OK)

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


def send_email(subject, message, recipient_list):
    from django.core.mail import send_mail
    send_mail(subject, message, 'no-reply@marketplace.com', recipient_list)

@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def approve_farmer(request, farmer_id):
    farmer = get_object_or_404(Farmer, id=farmer_id)
    farmer.is_approved = True
    farmer.save()

    # Notify farmer via email
    send_email(
        subject="Account Approved",
        message="Your account has been approved! You can now list products.",
        recipient_list=[farmer.user.email],
    )
    return Response({"detail": "Farmer approved successfully."})

@api_view(["POST"])
def create_farmer(request):
    serializer = FarmerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(["GET"])
def get_farmer(request):
    try:
        farmer = request.user.farmer  # Assumes Farmer is linked to the user
        serializer = FarmerSerializer(farmer)
        return Response(serializer.data)
    except AttributeError:
        return Response({"error": "You are not a farmer."}, status=403)

@api_view(["PUT"])
def update_farmer(request):
    try:
        farmer = request.user.farmer
        serializer = FarmerSerializer(farmer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    except AttributeError:
        return Response({"error": "You are not a farmer."}, status=403)
