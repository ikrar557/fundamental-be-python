from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from core.permissions import IsAdminOrSuperUser
from tickets.models import Ticket
from tickets.serializers import TicketSerializer

CACHE_KEY_LIST = "ticket_list"
CACHE_KEY_DETAIL = "ticket_detail_{}"

# Create your views here.
class TicketListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):

        tickets = cache.get(CACHE_KEY_LIST)

        if not tickets:
            print("Data diambil dari database")
            tickets = Ticket.objects.all().order_by('name')[:10]
            serializer = TicketSerializer(tickets, many=True)

            tickets_data = serializer.data

            cache.set(CACHE_KEY_LIST, tickets_data, timeout=3600)

            tickets = tickets_data
            data_source = "database"
        else:
            print("Data diambil dari cache")
            data_source = "cache"

        response = Response({"tickets": tickets})
        response["X-Data-Source"] = data_source
        return response

    def post(self, request):
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(CACHE_KEY_LIST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TicketDetailView(APIView):
    def get_object(self, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
            self.check_object_permissions(self.request, ticket)
            return ticket
        except Ticket.DoesNotExist:
            raise Http404

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        ticket_data = cache.get(cache_key)

        if not ticket_data:
            print(f"Ticket {pk} diambil dari database")
            ticket = self.get_object(pk)
            serializer = TicketSerializer(ticket)
            ticket_data = serializer.data
            cache.set(cache_key, ticket_data, timeout=3600)
            data_source = "database"
        else:
            print(f"Ticket {pk} diambil dari cache")
            data_source = "cache"

        response = Response(ticket_data)
        response["X-Data-Source"] = data_source
        return response

    def put(self, request, pk):
        ticket = self.get_object(pk)
        serializer = TicketSerializer(ticket, data=request.data)
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
