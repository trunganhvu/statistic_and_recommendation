from rest_framework import serializers
from mainApp.models import TimeLinePredicted

class TimeLinePredictedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeLinePredicted
        fields = '__all__'
