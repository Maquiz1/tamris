from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.models import CustomUser
from users.serializers import CustomUserSerializer, LoginSerializer, VerifyOTPSerializer, PasswordResetSerializer
import pyotp
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import CreateView
from django.urls import reverse_lazy
from users.forms import CustomUserCreationForm, CustomAuthenticationForm, OTPVerificationForm, PractitionerDocumentForm, CompanyDocumentForm, RoleSelectionForm, PractitionerDetailForm, CompanyDetailForm
from users.models import UserProfile, CompanyProfile
from users.emails import notify_staff_new_registration, notify_applicant_registration_status

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            if not user.is_email_verified:
                pass
            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token), 'user_id': user.id, 'role': user.role.name if user.role else None})
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp_code):
            user.is_email_verified = True
            user.save()
            return Response({'detail': 'OTP verified successfully. Email marked as verified.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            print(f'DEBUG: Password reset requested for {email}.')
            return Response({'detail': 'Password reset email sent (simulated).'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'If the email exists, a reset link will be sent.'}, status=status.HTTP_200_OK)

class FrontendRegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:frontend_verify_otp')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_email_verified:
                request.session['verify_email'] = request.user.email
                return redirect('users:frontend_verify_otp')
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.otp_secret = pyotp.random_base32()
        user.save()
        login(self.request, user)
        self.request.session['verify_email'] = user.email
        otp_code = pyotp.TOTP(user.otp_secret).now()
        print(f'DEBUG: Generated OTP for user {user.email} is {otp_code}')
        send_mail(subject='TAMRIS - Your OTP Verification Code', message=f'Welcome to TAMRIS! Your verification code is: {otp_code}\n\nThis code will expire in 5 minutes.', from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tamris.go.tz'), recipient_list=[user.email], fail_silently=True)
        messages.success(self.request, 'Account created successfully. An email with your OTP has been sent!')
        return redirect(self.success_url)

def frontend_login_view(request):
    if request.user.is_authenticated:
        if not request.user.is_email_verified:
            request.session['verify_email'] = request.user.email
            return redirect('users:frontend_verify_otp')
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if not user.is_email_verified:
                request.session['verify_email'] = user.email
                return redirect('users:frontend_verify_otp')
            return redirect('users:dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def frontend_logout_view(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('users:frontend_login')

@login_required
def verify_otp_view(request):
    user = request.user
    if user.is_email_verified:
        is_staff_role = user.role and user.role.name in ['Admin', 'Evaluator', 'Inspector', 'Finance Officer']
        if user.onboarding_step < 5 and (not is_staff_role) and (not user.is_superuser):
            return redirect('users:onboarding')
        return redirect('users:dashboard')
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save()
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp')
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(otp_code, valid_window=10):
                user.is_email_verified = True
                user.save()
                messages.success(request, 'OTP verified successfully!')
                is_staff_role = user.role and user.role.name in ['Admin', 'Evaluator', 'Inspector', 'Finance Officer']
                if user.onboarding_step < 5 and (not is_staff_role) and (not user.is_superuser):
                    return redirect('users:onboarding')
                return redirect('users:dashboard')
            else:
                messages.error(request, 'Invalid or expired OTP code. Please try again.')
    else:
        form = OTPVerificationForm()
        print(f'DEBUG: Current valid OTP for user {user.email} is {pyotp.TOTP(user.otp_secret).now()}')
    return render(request, 'users/verify_otp.html', {'form': form})
from django.http import JsonResponse

@login_required
def send_phone_otp_view(request):
    if request.method == 'POST':
        user = request.user
        if not user.phone_number:
            return JsonResponse({'success': False, 'error': 'No phone number associated with your profile.'})
        if user.is_phone_verified:
            return JsonResponse({'success': False, 'error': 'Phone number is already verified.'})
        if not user.phone_otp_secret:
            user.phone_otp_secret = pyotp.random_base32()
            user.save()
        otp_code = pyotp.TOTP(user.phone_otp_secret).now()
        print(f'DEBUG: Mock SMS sent to {user.phone_number} with OTP {otp_code}')
        return JsonResponse({'success': True, 'message': f'OTP sent to {user.phone_number}'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def verify_phone_otp_view(request):
    if request.method == 'POST':
        user = request.user
        otp_code = request.POST.get('otp_code', '').strip()
        if not user.phone_otp_secret:
            messages.error(request, 'Please request an OTP first.')
            return redirect('users:profile')
        totp = pyotp.TOTP(user.phone_otp_secret)
        if totp.verify(otp_code, valid_window=2):
            user.is_phone_verified = True
            user.save()
            messages.success(request, 'Your phone number has been successfully verified.')
        else:
            messages.error(request, 'Invalid or expired OTP code.')
        return redirect('users:profile')
    return redirect('users:profile')
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def resend_email_otp_view(request):
    user = request.user
    if user.is_email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('users:dashboard')
        
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save()
        
    otp_code = pyotp.TOTP(user.otp_secret).now()
    
    send_mail(
        subject='TAMRIS - Your OTP Verification Code',
        message=f'Welcome to TAMRIS! Your verification code is: {otp_code}\n\nThis code will expire in 5 minutes.',
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tamris.go.tz'),
        recipient_list=[user.email],
        fail_silently=True
    )
    
    messages.success(request, 'A new verification code has been sent to your email!')
    return redirect('users:frontend_verify_otp')