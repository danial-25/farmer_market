from rest_framework import status
from rest_framework.response import Response
from .models import *
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.reverse import reverse, reverse_lazy
from .serializers import *
from rest_framework import status, viewsets

from .forms import ProductForm
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage


def try_get_image_url(product):
    """
    Safely get the URL of the product image, handling cases where the file is missing.
    """
    try:
        # Check if the file exists in the storage system
        if product.image and FileSystemStorage().exists(product.image.name):
            return product.image.url
    except (ValueError, SuspiciousFileOperation):
        pass  # Handle any errors related to file paths or missing files
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def categories(request):
    categories = Category.objects.all()
    categories = CategorySerializer(categories, many=True)
    return Response(categories.data)


@api_view()
@permission_classes([IsAuthenticatedOrReadOnly])
def list(request):
    products = Product.objects.filter(quantity_available__gt=0)

    name_query = request.GET.get("name", "")
    description_query = request.GET.get("description", "")
    location_query = request.GET.get("location", "")
    category_query = request.GET.get("category", "")

    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    sort_by = request.GET.get("sort_by", "")
    if name_query:
        products = products.filter(name__icontains=name_query)

    if description_query:
        products = products.filter(description__icontains=description_query)

    if location_query:
        products = products.filter(farmer__location__icontains=location_query)

    if category_query:
        products = products.filter(category__name__iexact=category_query)
    # queryset=Product.objects.all().filter(category=category)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    if sort_by == "l2h":
        products = products.order_by("price")
    elif sort_by == "h2l":
        products = products.order_by("-price")
    elif sort_by == "popularity":
        products = products.order_by("-popularity")
    elif sort_by == "newest":
        products = products.order_by("-date_added")

    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def single(request, id):
    # Use get_object_or_404 to fetch the product or raise Http404 automatically
    queryset = get_object_or_404(Product, id=id)
    serializer = ProductSerializer(queryset, context={"request": request})
    return Response(serializer.data)


# Create a new product (only accessible to authenticated farmers)
@api_view(["POST"])
@permission_classes([IsAuthenticatedOrReadOnly])
def create_product(request):
    print(request.user)
    if not request.user.is_authenticated or not hasattr(request.user, "farmer_profile"):
        return Response(
            {"detail": "Authentication required."}, status=status.HTTP_403_FORBIDDEN
        )
    serializer = ProductCreateSerializer(
        data=request.data, context={"request": request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def farmer_dashboard(request):
    # Ensure the user is authenticated
    # print(request.user.farmer_profile)
    # print(Product.objects.filter(farmer=request.user.farmer_profile))
    if not request.user.is_authenticated:
        return Response(
            {"detail": "Authentication credentials were not provided."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Ensure the user is a farmer
    if not hasattr(request.user, "farmer_profile"):
        return Response(
            {"detail": "You are not authorized to access this dashboard."},
            status=status.HTTP_403_FORBIDDEN,
        )

    products = Product.objects.filter(farmer=request.user.farmer_profile)

    # Low-stock notification logic
    # low_stock_products = products.filter(quantity_available__lt=1000)

    data = {
        "farmer_name": request.user.farmer_profile.name,
        "total_products": products.count(),
        "products": [
            {
                "id": product.id,
                "name": product.name,
                "quantity_available": product.quantity_available,
                "image": (
                    (
                        product.image.url
                        if product.image and hasattr(product.image, "url")
                        else None
                    )
                    if try_get_image_url(product)
                    else None
                ),
                "price": product.price,
                "product_id": product.pid,
            }
            for product in products
        ],
    }
    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticatedOrReadOnly])
def mark_out_of_stock(request, product_id):
    """Mark a product as out of stock."""
    try:
        product = Product.objects.get(
            pid=product_id, farmer=request.user.farmer_profile
        )
        product.mark_out_of_stock()  # Mark as out of stock
        return Response({"message": "Product marked as out of stock."}, status=200)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found or you are not the owner."}, status=404
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticatedOrReadOnly])
def remove_product(request, product_id):
    """Remove a product from the marketplace."""
    try:
        product = Product.objects.get(
            pid=product_id, farmer=request.user.farmer_profile
        )
        product.remove_from_marketplace()  # Delete product
        return Response(
            {"message": "Product removed from the marketplace."}, status=200
        )
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found or you are not the owner."}, status=404
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_product(request, product_id):
    farmer = request.user.farmer_profile
    try:
        product = Product.objects.get(
            pid=product_id, farmer=request.user.farmer_profile
        )
        product.delete()
        return Response(
            {"message": "Product removed from the marketplace."}, status=200
        )
    except Product.DoesNotExist:
        return Response({"detail": "Product not found."}, status=404)


# @api_view(["PATCH"])
# @permission_classes([IsAuthenticated])
# def update_product(request, product_id):
#     try:
#         product = Product.objects.get(
#             pid=product_id, farmer=request.user.farmer_profile
#         )
#         data = request.data
#         product.name = data.get("name", product.name)
#         product.description = data.get("description", product.description)
#         product.price = data.get("price", product.price)
#         product.quantity_available = data.get(
#             "quantity_available", product.quantity_available
#         )
#         product.save()
#         return Response({"message": "Product updated successfully."}, status=200)
#     except Product.DoesNotExist:
#         return Response({"detail": "Product not found."}, status=404)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_product(request, product_id):
    try:
        # Retrieve the product owned by the authenticated farmer
        product = Product.objects.get(
            pid=product_id, farmer=request.user.farmer_profile
        )
    except Product.DoesNotExist:
        return Response(
            {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
        )

    # Use the serializer for partial updates
    serializer = ProductCreateSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()  # Save the updated product
        return Response(
            {"message": "Product updated successfully.", "product": serializer.data},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
