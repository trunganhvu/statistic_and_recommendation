from rest_framework import serializers
from mainApp.models import Major_Course

class TrainingframeworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Major_Course
        fields = '__all__'
