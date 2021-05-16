from rest_framework import serializers
from mainApp.models import Roles, Role_Function
 
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'

class RoleFunctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role_Function
        fields = '__all__'