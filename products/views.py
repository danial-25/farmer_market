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
from django.http import JsonResponse, HttpResponse
from .forms import ProductForm
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import FileSystemStorage
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO

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
        print("yo")
        return Response(
            {"message": "Product updated successfully.", "product": serializer.data},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




def inventory_report(request):
    # Retrieve start and end date from GET request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filter products by date range if provided
    products = Product.objects.all()
    if start_date and end_date:
        products = products.filter(date_added__gte=start_date, date_added__lte=end_date)
    
    # Process data to calculate low stock items and turnover rate
    report_data = process_inventory_data(products)
    
    # If "download" is specified in query parameters, return CSV or PDF
    if 'download' in request.GET:
        report_format = request.GET.get('format', 'pdf')
        if report_format == 'csv':
            return generate_csv_report(report_data)
        elif report_format == 'pdf':
            return generate_pdf_report(report_data)
    
    # If no download is requested, return data as JSON
    return JsonResponse(report_data)

# Helper function to process inventory data
def process_inventory_data(products):
    """ Process product data to identify low stock items and calculate turnover rate """
    low_stock_items = []
    total_available = 0
    total_sales = 0
    
    for product in products:
        if product.quantity_available < product.low_stock_threshold:
            low_stock_items.append({
                'name': product.name,
                'quantity_available': product.quantity_available,
                'low_stock_threshold': product.low_stock_threshold,
            })
        
        total_available += product.quantity_available
        total_sales += product.popularity  # Example: 'popularity' can represent sales

    turnover_rate = total_sales / total_available if total_available else 0

    return {
        'low_stock_items': low_stock_items,
        'turnover_rate': turnover_rate
    }

# Function to generate PDF report
def generate_pdf_report(report_data):
    """ Generate PDF file from the report data """
    low_stock_items = report_data['low_stock_items']
    
    # Check if data exists and is non-empty
    if not low_stock_items:
        return HttpResponse("No data to generate PDF", status=400)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Inventory Report - Low Stock Items")

    y_position = 730
    for item in low_stock_items:
        # Debugging: Ensure data is being passed correctly
        print(f"Generating PDF for: {item['name']} with Available: {item['quantity_available']} and Threshold: {item['low_stock_threshold']}")
        
        # Drawing the data onto the PDF
        p.drawString(100, y_position, f"Name: {item['name']}, Available: {item['quantity_available']}, Threshold: {item['low_stock_threshold']}")
        y_position -= 20

        # Check for page overflow
        if y_position < 50:
            p.showPage()  # Create a new page if overflow
            p.drawString(100, 750, "Inventory Report - Low Stock Items")
            y_position = 730
    
    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'
    return response