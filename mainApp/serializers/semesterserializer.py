from rest_framework import serializers
from mainApp.models import Semesters

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semesters
        fields = '__all__'
