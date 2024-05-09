from django.shortcuts import render,redirect
from django.db.models import Count, Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import VendorSerializer
from .models import *

def homepage(request):
    return render(request,"index.html")

def calculate_on_time_delivery_rate(vendor):
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed')
    total_completed_pos = completed_pos.count()
    on_time_delivered_pos = completed_pos.filter(delivery_date__lte=timezone.now()).count()
    if total_completed_pos == 0:
        return 0
    return (on_time_delivered_pos / total_completed_pos) * 100

def calculate_quality_rating_avg(vendor):
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed', quality_rating__isnull=False)
    return completed_pos.aggregate(Avg('quality_rating'))['quality_rating__avg'] or 0

def calculate_average_response_time(vendor):
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='completed', acknowledgment_date__isnull=False)
    total_completed_pos = completed_pos.count()
    if total_completed_pos == 0:
        return 0
    total_response_time_seconds = sum((po.acknowledgment_date - po.issue_date).total_seconds() for po in completed_pos)
    total_response_time_days = total_response_time_seconds / (total_completed_pos * 60 * 60 * 24)  # Convert seconds to days
    return '{:,.1f} days'.format(total_response_time_days)
    # return int(total_response_time_days)

def calculate_fulfillment_rate(vendor):
    total_pos = PurchaseOrder.objects.filter(vendor=vendor)
    total_po_count = total_pos.count()
    fulfilled_pos = total_pos.filter(status='completed')
    fulfilled_po_count = fulfilled_pos.count()
    if total_po_count == 0:
        return 0
    return (fulfilled_po_count / total_po_count) * 100


@api_view(['GET'])
def vendor_performance(request, vendor_id):
    try:
        vendor = Vendor.objects.get(id=vendor_id)
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)

    performance_metrics = {
        'on_time_delivery_rate': calculate_on_time_delivery_rate(vendor),
        'quality_rating_avg': calculate_quality_rating_avg(vendor),
        'average_response_time': calculate_average_response_time(vendor),
        'fulfillment_rate': calculate_fulfillment_rate(vendor)
    }
    return Response(performance_metrics)

@api_view(['POST'])
def acknowledge_purchase_order(request, po_id):
    try:
        po = PurchaseOrder.objects.get(id=po_id)
    except PurchaseOrder.DoesNotExist:
        return Response({'error': 'Purchase Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    po.acknowledgment_date = timezone.now()
    po.save()

    # Recalculate average_response_time
    vendor = po.vendor
    vendor.average_response_time = calculate_average_response_time(vendor)
    vendor.save()

    return Response({'message': 'Purchase Order acknowledged successfully'})

from rest_framework import generics
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer

class VendorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

class VendorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

class PurchaseOrderListCreateAPIView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

class PurchaseOrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

