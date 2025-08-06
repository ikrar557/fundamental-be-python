from django.http import Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from core.permissions import IsAdminOrSuperUser
from payments.models import Payment
from payments.serializers import PaymentSerializer

# Create your views here.
class PaymentListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):
        payments = Payment.objects.all().order_by('id')[:10]
        serializer = PaymentSerializer(payments, many=True)
        return Response({'payments': serializer.data})

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    def put(self, request, pk):
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(pk)
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
