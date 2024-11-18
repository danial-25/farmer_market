from rest_framework.response import Response
from .models import *
from django.shortcuts import get_object_or_404
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.reverse import reverse, reverse_lazy
from .serializers import *


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
