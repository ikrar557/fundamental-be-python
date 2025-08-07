from django.core.cache import cache
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from core.permissions import IsAdminOrSuperUser
from payments.models import Payment
from payments.serializers import PaymentSerializer

CACHE_KEY_LIST = "payment_list"
CACHE_KEY_DETAIL = "payment_detail_{}"

class PaymentListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):

        payments = cache.get(CACHE_KEY_LIST)

        if not payments:
            print("Data diambil dari database")
            payments = Payment.objects.all().order_by('id')[:10]
            serializer = PaymentSerializer(payments, many=True)

            payments_data = serializer.data

            cache.set(CACHE_KEY_LIST, payments_data, timeout=3600)

            payments = payments_data
            data_source = "database"
        else:
            print("Data diambil dari cache")
            data_source = "cache"

        response = Response({"payments": payments})
        response["X-Data-Source"] = data_source
        return response

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(CACHE_KEY_LIST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaymentDetailView(APIView):

    def get_object(self, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            self.check_object_permissions(self.request, payment)
            return payment
        except Payment.DoesNotExist:
            raise Http404

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        payment_data = cache.get(cache_key)

        if not payment_data:
            print(f"Payment {pk} diambil dari database")
            payment = self.get_object(pk)
            serializer = PaymentSerializer(payment)
            payment_data = serializer.data
            cache.set(cache_key, payment_data, timeout=3600)
            data_source = "database"
        else:
            print(f"Payment {pk} diambil dari cache")
            data_source = "cache"

        response = Response(payment_data)
        response["X-Data-Source"] = data_source
        return response

    def put(self, request, pk):
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(CACHE_KEY_LIST)
            cache.delete(CACHE_KEY_DETAIL.format(pk))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(pk)
        payment.delete()
        cache.delete(CACHE_KEY_LIST)
        cache.delete(CACHE_KEY_DETAIL.format(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)
