from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import User
from registrations.models import Registration
from tickets.models import Ticket

class RegistrationSerializer(serializers.HyperlinkedModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    ticket_id = serializers.PrimaryKeyRelatedField(queryset=Ticket.objects.all())
    ticket = serializers.CharField(source='ticket_id.name', read_only=True)
    user = serializers.CharField(source='user_id.username', read_only=True)
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = ('id', 'ticket', 'user', 'user_id', 'ticket_id', '_links')

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('registration-list', request=request),
                "action": "POST",
                "types": ["application/json"],
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "GET",
                "types": ["application/json"],
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "PUT",
                "types": ["application/json"],
            },
            {
                "rel": "self",
                "href": reverse('registration-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "types": ["application/json"],
            }
        ]