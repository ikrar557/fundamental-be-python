import uuid

from django.core.cache import cache
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

import registrations
from core.permissions import IsAdminOrSuperUser
from registrations.models import Registration
from registrations.serializers import RegistrationSerializer

from .tasks import send_ticket_email

CACHE_KEY_LIST = "registration_list"
CACHE_KEY_DETAIL = "registration_detail_{}"

class RegistrationListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):

        registrations = cache.get(CACHE_KEY_LIST)

        if not registrations:
            print("Data diambil dari database")
            registrations = Registration.objects.all().order_by('id')[:10]
            cache.get(CACHE_KEY_LIST)
            serializer = RegistrationSerializer(registrations, many=True)

            registrations_data = serializer.data

            cache.set(CACHE_KEY_LIST, registrations_data, timeout=3600)

            registrations = registrations_data
            data_source = "database"
        else:
            print("Data diambil dari database")
            data_source = "cache"

        response = Response({"registrations": registrations})
        response["X-Data-Source"] = data_source
        return response

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            registration = serializer.save()
            cache.delete(CACHE_KEY_LIST)
            print("Sending email via celery...")

            # TODO: Hapus jika collection sudah ditambahkan email
            user = registration.user_id
            if not user.email:
                random_email = f"test_{uuid.uuid4().hex[:6]}@mailtrap.io"
                user.email = random_email
                user.save()
                print(f"Email user kosong, diisi sementara dengan: {random_email}")

            send_ticket_email.delay(user.email, user.username, registration.id)

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
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        registration_data = cache.get(cache_key)

        if not registration_data:
            print(f"Registration {pk} diambil dari database")
            registration = self.get_object(pk)
            serializer = RegistrationSerializer(registration)
            registration_data = serializer.data
            cache.set(cache_key, registration_data, timeout=3600)
            data_source = "database"
        else:
            print("Registration {pk} diambil dari cache")
            data_source = "cache"

        response = Response(registration_data)
        response["X-Data-Source"] = data_source
        return response

    def put(self, request, pk):
        ticket = self.get_object(pk)
        serializer = RegistrationSerializer(ticket, data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(CACHE_KEY_LIST)
            cache.delete(CACHE_KEY_DETAIL.format(pk))
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = self.get_object(pk)
        ticket.delete()
        cache.delete(CACHE_KEY_LIST)
        cache.delete(CACHE_KEY_DETAIL.format(pk))
        return Response(status=status.HTTP_204_NO_CONTENT)