from rest_framework import serializers
from mainApp.models import Majors

class MajorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Majors
        fields = '__all__'
