from rest_framework import serializers
from mainApp.models import StudentGroups

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroups
        fields = '__all__'
