from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from .serializers import *
from products.serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

# from rest_framework.permissions import IsAdmin

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from products.models import Farm

from rest_framework.permissions import BasePermission
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import logging


class IsAdmin(BasePermission):
    """
    Custom permission to only allow admins to access certain views.
    """

    def has_permission(self, request, view):
        # Extract token from the request
        token_key = request.headers.get("Authorization", None)
        if not token_key:
            print("No Authorization token provided.")
            return False

        try:
            # Remove 'Bearer ' prefix if present
            token_key = token_key.replace("Token ", "")
            token = Token.objects.get(key=token_key)
            user = token.user

            # Ensure the role attribute exists and check if user is admin
            if hasattr(user, "role") and user.role == "admin":
                return True
            else:
                print(f"User {user.username} does not have admin role.")
                return False
        except (Token.DoesNotExist, User.DoesNotExist):
            print("Token or User does not exist.")
            return False


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    buyer = request.user.buyer_profile
    buyer = BuyerSerializer(buyer)
    return Response(buyer.data)


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

        elif user.role == "admin":
            # User is an admin
            return Response({"token": token.key, "role": "admin"}, status=200)

        else:
            return Response({"error": "User does not have a valid role."}, status=400)

    return Response({"error": "Invalid credentials"}, status=401)


def send_email(subject, message, recipient_list):
    from django.core.mail import send_mail

    send_mail(subject, message, "danial.sakhpantayev@gmail.com", recipient_list)


class FarmerProfile(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the farmer linked to the authenticated user
        farmer = request.user.farmer_profile
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the farmer's personal data
        farmer_serializer = FarmerSerializer(farmer)

        # Get the associated farm data (only name for now)
        try:
            farm = Farm.objects.get(farmer=farmer)
            farm_data = {"name": farm.name}
        except Farm.DoesNotExist:
            farm_data = {}
        # farm_data = {"name": Farm.objects.get(farmer=farmer).name}

        return Response({"farmer": farmer_serializer.data, "farm": farm_data})

    def patch(self, request):
        # Get the farmer linked to the authenticated user
        farmer = request.user.farmer_profile
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Update the farmer's personal information
        farmer_serializer = FarmerSerializer(farmer, data=request.data, partial=True)
        if farmer_serializer.is_valid():
            farmer_serializer.save()

        # Initialize farm_name to handle cases where farm does not exist
        farm_name = None

        # If farm name is provided, update it
        if "farm" in request.data and "name" in request.data["farm"]:
            try:
                # Attempt to retrieve the farm associated with the farmer
                farm = Farm.objects.get(farmer=farmer)
                farm.name = request.data["farm"]["name"]
                farm.save()
                farm_name = farm.name
            except Farm.DoesNotExist:
                # Handle case where no farm exists
                farm_name = None

        return Response({"farmer": farmer_serializer.data, "farm": {"name": farm_name}})


class FarmManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve farm details for the authenticated farmer."""
        try:

            farm = Farm.objects.get(farmer=request.user.farmer_profile)
            serializer = FarmSerializer(farm)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Farm.DoesNotExist:
            return Response(
                {"error": "No farm associated with this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request):
        """Add or update farm details for the authenticated farmer."""

        farmer = request.user.farmer_profile
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        farm = get_object_or_404(Farm, farmer=farmer)
        serializer = FarmSerializer(farm, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Farm details updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FarmerUpdateAPIView(APIView):
    permission_classes = [IsAdmin]  # Only accessible by admin users

    def get(self, request, id, *args, **kwargs):
        # Fetch the farmer by ID
        farmer = self.get_object(id)
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the farmer data
        serializer = FarmerSerializer(farmer)
        return Response(serializer.data)

    def get_object(self, id):
        try:
            return Farmer.objects.get(id=id)
        except Farmer.DoesNotExist:
            return None

    def patch(self, request, id, *args, **kwargs):
        # Fetch the farmer by ID (pk)
        farmer = self.get_object(id)
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize and validate the update data
        serializer = FarmerSerializer(
            farmer, data=request.data, partial=True
        )  # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        # Fetch the farmer by ID (pk)
        farmer = self.get_object(id)
        if farmer is None:
            return Response(
                {"detail": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete the farmer object
        farmer.user.delete()
        farmer.delete()
        return Response(
            {"detail": "Farmer deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )


# from django.shortcuts import render, redirect


# class FarmerEditView(APIView):
#     permission_classes = [IsAdmin]

#     def get(self, request, id, *args, **kwargs):
#         # Fetch the farmer by ID
#         farmer = self.get_object(id)
#         if farmer is None:
#             return redirect("farmer-list")  # Redirect to list if farmer is not found

#         # Render the edit form with farmer data
#         return render(request, "admin/farmer_edit.html", {"farmer": farmer})

#     def post(self, request, id, *args, **kwargs):
#         # Fetch the farmer by ID
#         farmer = self.get_object(id)
#         if farmer is None:
#             return redirect("farmers")

#         # Update the farmer's information
#         data = request.POST.dict()
#         data.pop("email", None)  # Exclude email from the data
#         data.pop("user", None)
#         data["user"] = farmer.user
#         serializer = FarmerSerializer(farmer, data=request.POST, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return redirect(
#                 "farmers"
#             )  # Redirect to farmer list after successful update

#         # Render form with errors if validation fails
#         return render(
#             request,
#             "admin/farmer_edit.html",
#             {"farmer": farmer, "errors": serializer.errors},
#         )

#     def get_object(self, id):
#         try:
#             return Farmer.objects.get(id=id)
#         except Farmer.DoesNotExist:
#             return None


# class FarmerDeleteAPIView(APIView):
#     permission_classes = [IsAdmin]

#     def post(self, request, id, *args, **kwargs):
#         # Fetch the farmer by ID
#         farmer = self.get_object(id)
#         if farmer is None:
#             return redirect("farmers")  # Redirect to the farmer list even if not found

#         # Delete the farmer object
#         farmer.user.delete()
#         farmer.delete()

#         # Redirect to the farmer list page
#         return redirect("farmers")

#     def get_object(self, id):
#         try:
#             return Farmer.objects.get(id=id)
#         except Farmer.DoesNotExist:
#             return None


@api_view(["GET"])
@permission_classes([IsAdmin])
def list_farmers(request):
    farmers = Farmer.objects.all()
    serialized_farmers = FarmerSerializer(farmers, many=True).data

    # Add user details dynamically to the serialized farmers
    for farmer_data, farmer_instance in zip(serialized_farmers, farmers):
        user = farmer_instance.user
        # user = farmer_instance.user
        if user:
            farmer_data["user"] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,  # Assuming 'role' exists on the CustomUser model
                "is_active": user.is_active,
            }
        else:
            farmer_data["user"] = None

    return Response(serialized_farmers)
    # return render(request, 'templates/admin/list_farmers.html', {'farmers': farmers})
    # return render(request, "admin/list_farmers.html", {"farmers": farmers})


class BuyerUpdateAPIView(APIView):
    permission_classes = [IsAdmin]  # Only accessible by admin users

    def get_object(self, id):
        try:
            return Buyer.objects.get(id=id)
        except Buyer.DoesNotExist:
            return None

    def get(self, request, id, *args, **kwargs):
        # Fetch the buyer by ID
        buyer = self.get_object(id)
        if buyer is None:
            return Response(
                {"detail": "Buyer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the buyer data
        serializer = BuyerSerializer(buyer)
        return Response(serializer.data)

    def patch(self, request, id, *args, **kwargs):
        # Fetch the buyer by ID
        buyer = self.get_object(id)
        if buyer is None:
            return Response(
                {"detail": "Buyer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize and validate the update data
        serializer = BuyerSerializer(
            buyer, data=request.data, partial=True
        )  # partial=True allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        # Fetch the buyer by ID
        buyer = self.get_object(id)
        if buyer is None:
            return Response(
                {"detail": "Buyer not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete the buyer object along with the associated user
        buyer.user.delete()
        buyer.delete()
        return Response(
            {"detail": "Buyer deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )


@api_view(["GET"])
@permission_classes([IsAdmin])  # Only admin users can view all buyers
def list_buyers(request):
    buyers = Buyer.objects.all()
    serialized_buyers = BuyerSerializer(buyers, many=True).data

    # Add user details dynamically to the serialized buyers
    for buyer_data, buyer_instance in zip(serialized_buyers, buyers):
        user = buyer_instance.user
        buyer_data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,  # Assuming 'role' exists on the CustomUser model
            "is_active": user.is_active,
        }

    return Response(serialized_buyers)


class PendingFarmersAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, id=None):
        print("lol")
        # If `id` is provided, get a specific farmer, else list all pending farmers
        if id:
            try:
                farmer = Farmer.objects.get(id=id, is_pending=True)
                serialized_farmer = FarmerSerializer(farmer).data
                return Response(serialized_farmer)
            except Farmer.DoesNotExist:
                return Response(
                    {"detail": "Farmer not found or not pending."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # List all pending farmers
            pending_farmers = Farmer.objects.filter(is_pending=True)
            serialized_farmers = FarmerSerializer(pending_farmers, many=True).data
            return Response(serialized_farmers)

    def patch(self, request, id):
        farmer = Farmer.objects.get(id=id)

        if "approve" in request.data:
            farmer.is_pending = False
            farmer.is_approved = True
            send_email(
                subject="Account Approve",
                message="Your account has been approved! You can now list products.",
                recipient_list=[farmer.user.email],
            )
            farmer.save()
            return Response({"message": "Farmer approved."}, status=status.HTTP_200_OK)

        elif "reject" in request.data:
            farmer.is_pending = False
            farmer.is_approved = False
            rejection_reason = request.data.get("reason", "No reason provided.")
            send_email(
                subject="Account Reject",
                message=f"Your account has been rejected. Reason: {rejection_reason}",
                recipient_list=[farmer.user.email],
            )
            farmer.save()
            return Response({"message": "Farmer rejected."}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_cart(request):
    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED
        )

    cart, created = Cart.objects.get_or_create(buyer=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def add_to_cart(request):

    try:
        # Extract product ID and quantity from the request
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)  # Default to 1 if not provided

        # Validate the product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Get or create a cart for the logged-in user
        cart, _ = Cart.objects.get_or_create(buyer=request.user)

        # Get or create the cart item
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            # If the item already exists, update the quantity
            cart_item.quantity += int(quantity)
        else:
            cart_item.quantity = int(quantity)

        cart_item.save()

        return Response(
            {
                "detail": "Item added to cart successfully.",
                "cart_item": {
                    "product": product.name,
                    "quantity": cart_item.quantity,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"detail": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def apply_promo_code(request):
    # Placeholder for promo code logic
    promo_code = request.data.get("promo_code")
    # Validate and apply promo code here
    return Response(
        {"detail": "Promo code applied successfully."}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    if request.method == "POST":
        # Pass the request context to the serializer
        serializer = OrderSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlaceOrderView(generics.CreateAPIView):
    serializer_class = OrderSerializer

    def get_serializer_context(self):
        # Ensure 'request' is passed in the context
        context = super().get_serializer_context()
        context["request"] = self.request  # Explicitly set the request
        return context

    def perform_create(self, serializer):
        # You can pass the user explicitly as well when saving
        user = self.request.user
        serializer.save(buyer=user)
        order = serializer.save(buyer=user)
        order.calculate_total()  # This will update the total_price field
        order.save()


class OrderTrackingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            return Response(
                {
                    "order_id": order.id,
                    "status": order.status,
                    "total_price": order.total_price,
                }
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)


logger = logging.getLogger(__name__)


class ChangeOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, order_id):
        order = Order.objects.get(id=order_id)
        status = request.data.get("status")

        # Update the order status
        order.status = status
        order.save()

        # Send the email notification
        try:
            send_mail(
                "Order Status Update",
                f"Your order {order_id} status is now: {status}.",
                os.getenv("EMAIL_HOST_USER"),
                [order.buyer.email],  # Assuming the buyer is linked to the order
                fail_silently=False,
            )
            logger.info(f"Email sent to {order.buyer.email} for order {order_id}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")

        return Response({"message": "Order status updated and notification sent."})


class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current authenticated user
        buyer = request.user

        # Filter orders by the buyer (user)
        orders = Order.objects.filter(buyer=buyer).order_by(
            "-order_date"
        )  # Order by most recent

        # Serialize the order data
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


# @api_view(["POST"])
# def create_farmer(request):
#     serializer = FarmerSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(["GET"])
# def get_farmer(request):
#     try:
#         farmer = request.user.farmer  # Assumes Farmer is linked to the user
#         serializer = FarmerSerializer(farmer)
#         return Response(serializer.data)
#     except AttributeError:
#         return Response({"error": "You are not a farmer."}, status=403)


# @api_view(["PUT"])
# def update_farmer(request):
#     try:
#         farmer = request.user.farmer
#         serializer = FarmerSerializer(farmer, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=400)
#     except AttributeError:
#         return Response({"error": "You are not a farmer."}, status=403)
