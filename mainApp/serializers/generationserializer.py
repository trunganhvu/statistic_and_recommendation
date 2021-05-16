from rest_framework import serializers
from mainApp.models import Generations

class GenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Generations
        fields = '__all__'
