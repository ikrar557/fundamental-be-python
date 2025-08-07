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
from loguru import logger

CACHE_KEY_LIST = "ticket_list"
CACHE_KEY_DETAIL = "ticket_detail_{}"


class TicketListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):
        tickets = cache.get(CACHE_KEY_LIST)
        data_source = "cache"

        if not tickets:
            data_source = "database"
            logger.info("GET /tickets - Cache miss. Retrieving list from DB for user {}", request.user)
            tickets_qs = Ticket.objects.all().order_by('name')[:10]
            serializer = TicketSerializer(tickets_qs, many=True)
            tickets = serializer.data
            cache.set(CACHE_KEY_LIST, tickets, timeout=3600)
        else:
            logger.info("GET /tickets - Cache hit. Retrieving list from cache for user {}", request.user)

        response = Response({"tickets": tickets})
        response["X-Data-Source"] = data_source
        return response

    def post(self, request):
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            ticket = serializer.save()
            cache.delete(CACHE_KEY_LIST)
            logger.info("POST /tickets - New ticket '{}' created by admin {}", ticket.name, request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        logger.error("POST /tickets - Ticket creation failed by admin {}. Errors: {}", request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TicketDetailView(APIView):
    def get_object(self, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
            # Izin objek diperiksa dalam metode view yang memerlukan (PUT, DELETE)
            return ticket
        except Ticket.DoesNotExist:
            logger.warning("Ticket with pk={} not found, requested by {}", pk, self.request.user)
            raise Http404

    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated(), IsAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        ticket_data = cache.get(cache_key)
        data_source = "cache"

        if not ticket_data:
            data_source = "database"
            logger.info("GET /tickets/{} - Cache miss. Retrieving detail from DB for user {}", pk, request.user)
            ticket = self.get_object(pk)
            serializer = TicketSerializer(ticket)
            ticket_data = serializer.data
            cache.set(cache_key, ticket_data, timeout=3600)
        else:
            logger.info("GET /tickets/{} - Cache hit. Retrieving detail from cache for user {}", pk, request.user)

        response = Response(ticket_data)
        response["X-Data-Source"] = data_source
        return response

    def put(self, request, pk):
        ticket = self.get_object(pk)
        self.check_object_permissions(request, ticket)
        serializer = TicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            updated_ticket = serializer.save()
            cache.delete(CACHE_KEY_LIST)
            cache.delete(CACHE_KEY_DETAIL.format(pk))
            logger.info("PUT /tickets/{} - Ticket '{}' updated by admin {}", pk, updated_ticket.name, request.user)
            return Response(serializer.data)

        logger.error("PUT /tickets/{} - Update for ticket '{}' failed by admin {}. Errors: {}", pk, ticket.name,
                     request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ticket = self.get_object(pk)
        self.check_object_permissions(request, ticket)
        ticket_name = ticket.name
        ticket.delete()
        cache.delete(CACHE_KEY_LIST)
        cache.delete(CACHE_KEY_DETAIL.format(pk))
        logger.info("DELETE /tickets/{} - Ticket '{}' deleted by admin {}", pk, ticket_name, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)