from django.http import Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.permissions import IsAdminOrSuperUser
from registrations.models import Registration
from registrations.serializers import RegistrationSerializer

# Create your views here.
class RegistrationListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):
        registrations = Registration.objects.all().order_by('id')[:10]
        serializer = RegistrationSerializer(registrations, many=True)
        return Response({'registrations': serializer.data})

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegistrationDetailView(APIView):
    def get_object(self, pk):
        try:
            registration = Registration.objects.get(pk=pk)
            self.check_object_permissions(self.request, registration)
            return registration
        except Registration.DoesNotExist:
            raise Http404

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        registration = self.get_object(pk)
        serializer = RegistrationSerializer(registration)
        return Response(serializer.data)

    def put(self, request, pk):
        ticket = self.get_object(pk)
        serializer = RegistrationSerializer(ticket, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = self.get_object(pk)
        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)