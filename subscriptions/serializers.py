from rest_framework import serializers
from subscriptions.models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["id", "user", "subscription_id", "plan_id", "status", "start_date", "expiry_date"]
        read_only_fields = ["status", "start_date", "expiry_date"]
