from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, TokenBlacklistSerializer
from rest_framework import serializers
from accounts.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)
    created_by = serializers.SerializerMethodField()
    edited_by = serializers.SerializerMethodField()
    roles_label = serializers.CharField(source='get_roles_display', read_only=True)
    registered_via_label = serializers.CharField(source='get_registered_via_display', read_only=True)
    pabrik = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'name', 'roles', 'is_active', 'is_superuser',
            'roles_label', 'ketua_kelompok_tani', 'registered_via', 'registered_via_label',
            'pabrik', 'created_by', 'edited_by', 'updated_at'
        )
        read_only_fields = ('id', 'is_active')
    
    def get_created_by(self, obj):
        return ""

    def get_edited_by(self, obj):
        return ""

    def get_pabrik(self, obj):
        if obj.pabrik:
            return {'id': obj.pabrik.id, 'nama': obj.pabrik.nama}
        return None
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_serializer = UserSerializer(self.user)
        data.update(user_serializer.data)
        data['full_name'] = self.user.get_full_name()
        
        custom_response = {
            "status": "success",
            "message": "Success Login",
            "data": data
        }
        return custom_response


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        custom_response = {
            "status": "success",
            "message": "Token refreshed successfully",
            "data": {
                "access": data.get("access"),
            }
        }

        return custom_response


class CustomTokenBlacklistSerializer(TokenBlacklistSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        custom_response = {
            "status": "success",
            "message": "Token blacklisted successfully",
            "data": {
                "detail": data.get("detail", "Token blacklisted successfully"),
            }
        }

        return custom_response
