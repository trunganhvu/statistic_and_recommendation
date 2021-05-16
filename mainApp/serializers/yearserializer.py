from rest_framework import serializers
from mainApp.models import Years

class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Years
        fields = '__all__'
