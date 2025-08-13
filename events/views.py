import tempfile
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.permissions import IsOwnerOrAdminOrSuperUser, IsAdminOrSuperUser
from events.models import Event
from events.serializers import EventSerializer, EventPosterSerializer

from minio import Minio
import os
from loguru import logger

def get_minio_client():
    return Minio(
        endpoint=os.getenv('MINIO_ENDPOINT_URL'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

bucket_name = os.getenv('MINIO_BUCKET_NAME')
CACHE_KEY_LIST = "event_list"
CACHE_KEY_DETAIL = "event_detail_{}"

class EventListCreateView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get(self, request):
        events = cache.get(CACHE_KEY_LIST)
        if events:
            logger.info("GET /events - Data retrieved from cache by {}", request.user)
            return Response(events)
        if not events:
            print("Data diambil dari database")
            events = Event.objects.all().order_by('name')[:10]
            cache.get(CACHE_KEY_LIST)
            serializer = EventSerializer(events, many=True)
            events_data = serializer.data
            cache.set(CACHE_KEY_LIST, events_data, timeout=3600)
            logger.info("GET /events - Data retrieved from DB by {}", request.user)
            events = events_data
            data_source = "database"
        else:
            print("Data diambil dari cache")
            logger.info("GET /events - Data retrieved from Cache by {}", request.user)
            data_source = "cache"
        response = Response({"events": events})
        response["X-Data-Source"] = data_source
        return response

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            event = serializer.save()
            cache.delete(CACHE_KEY_LIST)
            logger.info("POST /events - Event '{}' created by {}", event.name, request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error("POST /events - Validation failed by {}: {}", request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsOwnerOrAdminOrSuperUser()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            event = Event.objects.get(pk=pk)
            self.check_object_permissions(self.request, event)
            return event
        except Event.DoesNotExist:
            logger.warning("Event with pk={} not found, requested by {}", pk, self.request.user)
            raise Http404

    def get(self, request, pk):
        cache_key = CACHE_KEY_DETAIL.format(pk)
        event_data = cache.get(cache_key)
        if not event_data:
            print(f"Event {pk} diambil dari database")
            logger.info("GET /events/{} - Cache miss. Retrieving from DB for user {}", pk, request.user)
            event = self.get_object(pk)
            serializer = EventSerializer(event)
            event_data = serializer.data
            cache.set(cache_key, event_data, timeout=3600)
            data_source = "database"
        else:
            print(f"Event {pk} diambil dari cache")
            logger.info("GET /events/{} - Cache hit. Retrieving from cache for user {}", pk, request.user)
            data_source = "cache"
        response = Response(event_data)
        response["X-Data-Source"] = data_source
        return response

    def put(self, request, pk):
        event = self.get_object(pk)
        serializer = EventSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(CACHE_KEY_LIST)
            cache.delete(CACHE_KEY_DETAIL.format(pk))
            logger.info("Updating event with ID {} with data: {}", pk, request.data)
            return Response(serializer.data)
        logger.error("PUT /events/{} - Update for event {} failed by {}. Errors: {}", pk, pk, request.user, serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        event.delete()
        cache.delete(CACHE_KEY_LIST)
        cache.delete(CACHE_KEY_DETAIL.format(pk))
        logger.info("Deleting event with ID {}", pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

class EventPosterView(APIView):
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [IsAuthenticated(), IsAdminOrSuperUser()]

    def post(self, request):
        serializer = EventPosterSerializer(data=request.data)
        file = request.FILES.get('image')
        if serializer.is_valid():
            serializer.save()
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp.flush()
                    tmp_path = tmp.name
                object_name = f"{serializer.instance.image.name}"
                client = get_minio_client()
                client.fput_object(
                    bucket_name,
                    object_name,
                    tmp_path,
                    content_type=file.content_type
                )
                logger.info(f"Event poster uploaded: {object_name} by {request.user.username}")
            except Exception as e:
                logger.error(f"Upload to Minio failed: {e}")
                return Response({'error': f"Upload to Minio Failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid EventPoster data submitted by {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventPosterDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        images = event.posters.all()
        logger.info("GET /events/{}/posters - User {} requests {} poster(s).", pk, request.user, images.count())
        serialized_images = []
        for image in images:
            try:
                client = get_minio_client()
                presigned_url = client.presigned_get_object(
                    bucket_name,
                    image.image.name,
                    response_headers={"response-content-type": "image/jpeg"}
                )
                serialized_images.append({"id": image.id, "url": presigned_url})
            except Exception as e:
                logger.error("Failed to get presigned URL for image '{}' in event {}. Error: {}", image.image.name, pk, e)
                continue
        return Response(serialized_images)