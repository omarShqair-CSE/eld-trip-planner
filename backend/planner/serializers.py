from rest_framework import serializers


class TripSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=200)
    pickup_location = serializers.CharField(max_length=200)
    dropoff_location = serializers.CharField(max_length=200)
    cycle_used = serializers.FloatField(min_value=0, max_value=70)
    start_time = serializers.CharField(required=False, allow_blank=True)