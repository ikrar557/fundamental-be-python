from rest_framework import serializers
from rest_framework.reverse import reverse

from events.models import Event
from tickets.models import Ticket

class TicketSerializer(serializers.HyperlinkedModelSerializer):
    event = serializers.CharField(source='event_id.name', read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), write_only=True)
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'name', 'price', 'sales_start', 'sales_end', 'quota', 'event', 'event_id', '_links']

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('ticket-list', request=request),
                "action": "POST",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('ticket-detail', kwargs={'pk': obj.id}, request=request),
                "action": "GET",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('ticket-detail', kwargs={'pk': obj.id}, request=request),
                "action": "PUT",
                "types": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('ticket-detail', kwargs={'pk': obj.id}, request=request),
                "action": "DELETE",
                "types": ["application/json"]
            }
        ]