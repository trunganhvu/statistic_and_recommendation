from rest_framework import serializers
from mainApp.models import Functions

class FunctionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Functions
        fields = '__all__'
