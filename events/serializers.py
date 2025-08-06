from rest_framework import serializers
from rest_framework.reverse import reverse

from dicoevent import settings
from .models import Event, EventPoster
from core.models import User

class EventSerializer(serializers.HyperlinkedModelSerializer):
    organizer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'location', 'start_time', 'end_time', 'status', 'quota', 'category', 'organizer_id', '_links']

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('event-list', request=request),
                "action": "POST",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk':obj.pk}, request=request),
                "action": "GET",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk':obj.pk}, request=request),
                "action": "PUT",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('event-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "types": ["application/json"]
            },
        ]

class EventPosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPoster
        fields = ['id', 'event', 'image']

    def validate_image(self, image):
        max_size = settings.MAX_IMAGE_SIZE
        if image.size > max_size:
            raise serializers.ValidationError("Image size cannot exceed 500 kB.")
        return image
