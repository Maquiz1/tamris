from rest_framework import serializers
from .models import CustomUser, Role, UserProfile, CompanyProfile
from rest_framework_simplejwt.tokens import RefreshToken
import pyotp

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'nida_number', 'address', 'tahpc_certificate']

class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = ['company_name', 'brela_number', 'tin', 'business_license', 'physical_address']

class CustomUserSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(required=False)
    company_profile = CompanyProfileSerializer(required=False)
    role = serializers.SlugRelatedField(slug_field='name', queryset=Role.objects.all())

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'role', 'is_email_verified', 'user_profile', 'company_profile', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_email_verified': {'read_only': True}
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('user_profile', None)
        company_data = validated_data.pop('company_profile', None)
        password = validated_data.pop('password')
        
        user = CustomUser(**validated_data)
        user.set_password(password)
        # Generate OTP secret for the new user
        user.otp_secret = pyotp.random_base32()
        user.save()

        # Handle nested profiles based on role
        if profile_data and user.role.name == 'Individual Applicant': # Example logic
            UserProfile.objects.create(user=user, **profile_data)
        elif company_data and user.role.name == 'Company Applicant':
            CompanyProfile.objects.create(user=user, **company_data)

        # In a real app, you would trigger an email/SMS sending the OTP here
        print(f"DEBUG: Generated OTP for user {user.email} is {pyotp.TOTP(user.otp_secret).now()}")
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
