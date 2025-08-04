from rest_framework.reverse import reverse
from rest_framework import serializers

from payments.models import Payment
from registrations.models import Registration
from registrations.serializers import RegistrationSerializer


class PaymentSerializer(serializers.HyperlinkedModelSerializer):
    _links = serializers.SerializerMethodField()
    registration = serializers.CharField(source='registration_id.id', read_only=True)
    registration_id = serializers.PrimaryKeyRelatedField(
        queryset=Registration.objects.all(),
        write_only=True
    )

    class Meta:
        model = Payment
        fields = ('id', 'payment_method', 'payment_status', 'amount_paid', 'registration', 'registration_id', '_links')

    def get__links(self, obj):
        request = self.context.get('request')
        return [
            {
                "rel": "self",
                "href": reverse('payment-list', request=request),
                "action": "POST",
                "type": ["application/json"]
            },
            {
                "rel": "self",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "GET",
                "type": ["application/json"]
            }
            ,
            {
                "rel": "self",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "PUT",
                "type": ["application/json"]
            }
            ,
            {
                "rel": "self",
                "href": reverse('payment-detail', kwargs={'pk': obj.pk}, request=request),
                "action": "DELETE",
                "type": ["application/json"]
            }

        ]