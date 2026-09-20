from rest_framework import serializers
from .models import CustomUser, Role, Applicant, Individual, Organization
from rest_framework_simplejwt.tokens import RefreshToken
import pyotp

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']

class IndividualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Individual
        fields = ['first_name', 'last_name', 'sex', 'date_of_birth']

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['organization_name', 'organization_type', 'registration_number', 'tin']

    def validate_tin(self, value):
        if value:
            return value.replace('-', '').replace(' ', '')
        return value

class ApplicantSerializer(serializers.ModelSerializer):
    individual = IndividualSerializer(required=False)
    organization = OrganizationSerializer(required=False)

    class Meta:
        model = Applicant
        fields = ['applicant_type', 'application_no', 'status', 'individual', 'organization']

class CustomUserSerializer(serializers.ModelSerializer):
    applicant_profile = ApplicantSerializer(required=False)
    role = serializers.SlugRelatedField(slug_field='name', queryset=Role.objects.all())

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'role', 'is_email_verified', 'applicant_profile', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_email_verified': {'read_only': True}
        }

    def validate_phone_number(self, value):
        if value:
            return value.replace('-', '').replace(' ', '')
        return value

    def create(self, validated_data):
        applicant_data = validated_data.pop('applicant_profile', None)
        password = validated_data.pop('password')
        
        user = CustomUser(**validated_data)
        user.set_password(password)
        # Generate OTP secret for the new user
        user.otp_secret = pyotp.random_base32()
        user.save()

        if applicant_data:
            individual_data = applicant_data.pop('individual', None)
            organization_data = applicant_data.pop('organization', None)
            applicant = Applicant.objects.create(user=user, **applicant_data)
            if applicant.applicant_type == 'Individual' and individual_data:
                Individual.objects.create(applicant=applicant, **individual_data)
            elif applicant.applicant_type == 'Organization' and organization_data:
                Organization.objects.create(applicant=applicant, **organization_data)

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
