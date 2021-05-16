from rest_framework import serializers
from mainApp.models import Logs

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logs
        fields = '__all__'
