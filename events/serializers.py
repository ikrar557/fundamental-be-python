from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Event
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