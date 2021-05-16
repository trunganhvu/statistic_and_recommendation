from rest_framework import serializers
from mainApp.models import CustomUser, Profiles

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # fields = ('id','password','last_login','username','date_joined', 'role', 'profile')
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profiles
        fields = '__all__'
