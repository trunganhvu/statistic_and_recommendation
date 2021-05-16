from rest_framework import serializers
from mainApp.models import Units

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Units
        fields = '__all__'
