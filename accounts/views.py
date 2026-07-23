from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from rest_framework import generics
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from accounts.serializers import (
    CustomTokenObtainPairSerializer, CustomTokenRefreshSerializer, CustomTokenBlacklistSerializer,
    UserSerializer
)
from accounts.forms import (
    PasswordResetForm, RegisterRequestForm, RegisterConfirmForm, ChangePasswordForm, UserCreateForm,
    UserUpdateForm, UserProfileUpdateForm
)
from accounts.models import RequestOTP, RequestOTP, CustomUser
from utils import str_to_bool
from utils.serializers import custom_response
from utils.decorators import role_required
from utils.choices import RequestOTPVia, RegisteredVia, UserRole
from utils import PaginationDefault
from post_office import mail


User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class MobileCustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer


class CustomTokenBlacklistView(TokenBlacklistView):
    serializer_class = CustomTokenBlacklistSerializer


class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(custom_response(status='error', message='Email is required', 
                                            errors={'email': 'This field is required.'}),
                            status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(custom_response(
                status='error', 
                message='User not found with this email address',
            ), status=status.HTTP_400_BAD_REQUEST)
            
        password_otp = RequestOTP.create_otp(identifier=email)
        
        mail.send(
            [email],
            settings.DEFAULT_FROM_EMAIL,
            subject='OTP Reset your password',
            message=f'Insert the OTP on your app: {password_otp.otp}',  # You can customize this message
            priority='now',
        )
        
        return Response(custom_response(
            status='success', 
            message='If the email exists, a reset OTP will be sent.',
            data={'otp_token': password_otp.token}
        ), status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    def post(self, request):
        otp = request.data.get('otp')
        token = request.data.get('otp_token')
        try:
            obj = RequestOTP.objects.get(token=token, otp=otp, is_used=False)
        except RequestOTP.DoesNotExist:
            return Response(custom_response(status='error', message='Invalid OTP or token'),
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(custom_response(status='success', message='OTP valid', data={'otp_token': token}),
                        status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):

    def post(self, request):
        form = PasswordResetForm(request.data)
        if not form.is_valid():
            return Response(
                custom_response(status='error', message='Invalid Request. Please check your data',
                                errors=form.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        password = form.cleaned_data['password']
        token = form.cleaned_data['otp_token']
        otp = form.cleaned_data['otp']
        
        try:
            obj = RequestOTP.objects.get(token=token, otp=otp,  is_used=False)
        except RequestOTP.DoesNotExist:
            return Response(custom_response(status='error', message='Invalid or expired token'),
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if obj.via == RequestOTPVia.EMAIL:   
                user = get_user_model().objects.get(email=obj.identifier)
            else:
                return Response(custom_response(status='error', 
                                                message='Request OTP saat ini hanya tersedia untuk Email'),
                                status=status.HTTP_400_BAD_REQUEST)
        except get_user_model().DoesNotExist:
            return Response(custom_response(status='error', message='User not found'),
                            status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(password)
        user.email_is_valid = True # type: ignore
        user.save()
        obj.is_used = True
        obj.save()
        return Response(custom_response(status='success', message='Password has been reset'),
                        status=status.HTTP_200_OK)


class RegisterRequestView(APIView):
    
    def post(self, request):
        form = RegisterRequestForm(request.data)
        if not form.is_valid():
            return Response(
                custom_response(status='error', message='Invalid Request. Please check your data',
                                errors=form.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        email = form.cleaned_data['email']
        register_otp = RequestOTP.create_otp(identifier=email)
        
        mail.send(
            [email],
            settings.DEFAULT_FROM_EMAIL,
            subject='OTP Registration',
            message=f'Insert the OTP on your app: {register_otp.otp}',  # You can customize this message
            priority='now',
        )
        
        return Response(custom_response(
            status='success', 
            message='If the email valid, a register OTP will be sent.',
            data={'otp_token': register_otp.token}
        ), status=status.HTTP_200_OK)


class RegisterConfirmView(APIView):

    def post(self, request):
        form = RegisterConfirmForm(request.data)
        if not form.is_valid():
            return Response(
                custom_response(status='error', message='Invalid Request. Please check your data',
                                errors=form.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        token = form.cleaned_data['otp_token']
        otp = form.cleaned_data['otp']
            
        try:
            obj = RequestOTP.objects.get(token=token, otp=otp, is_used=False)
        except RequestOTP.DoesNotExist:
            return Response(custom_response(status='error', message='Invalid or expired token'),
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Check request device from user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'android' in user_agent:
            platform = RegisteredVia.ANDROID
        elif 'iphone' in user_agent or 'ios' in user_agent:
            platform = RegisteredVia.IOS
        elif 'windows' in user_agent or 'macintosh' in user_agent or 'linux' in user_agent:
            platform = RegisteredVia.WEB_ADMIN
        else:
            platform = RegisteredVia.WEB_ADMIN

        with transaction.atomic():
            user = form.create_user(registered_via=platform)
            user.email_is_valid = True # type: ignore
            if platform in [RegisteredVia.ANDROID, RegisteredVia.IOS]:
                user.role = UserRole.PEKEBUN
            user.save()
            
            obj.is_used = True
            obj.save()

        return Response(custom_response(status='success', message='Successfuly create new user'),
                        status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = ChangePasswordForm(data=request.data, user=request.user)
        if form.is_valid():
            form.save()
            return Response(custom_response(status='success', message='Kata sandi berhasil diubah'),
                            status=status.HTTP_200_OK)
            
        return Response(
            custom_response(status='error', message='Gagal mengubah kata sandi. Periksa data Anda',
                            errors=form.errors),
            status=status.HTTP_400_BAD_REQUEST
        )        


class UserCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def post(self, request):
        form = UserCreateForm(request.data)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
            serializer = UserSerializer(user)
            data = serializer.data
            return Response(custom_response(status='success', message='Berhasil membuat pengguna baru', data=data),
                        status=status.HTTP_200_OK)
        
        return Response(
            custom_response(status='error', message='Permintaan tidak valid. Silakan periksa data Anda.',
                            errors=form.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class UserUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def get_data_post(self, request):
        data = request.data.copy()
        data['is_active'] = str_to_bool(data['is_active'])
        return data
    
    def post(self, request):
        data = self.get_data_post(request)
        try:
            user = User.objects.get(id=data['id'])
        except User.DoesNotExist:
            return Response(custom_response(status='error', message='Pengguna tidak ditemukan'),
                            status=status.HTTP_404_NOT_FOUND)

        form = UserUpdateForm(data, user=user)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
            
            serializer = UserSerializer(user)
            data = serializer.data
            return Response(custom_response(status='success', message='Berhasil ubah data pengguna', data=data),
                        status=status.HTTP_200_OK)
        
        return Response(
            custom_response(status='error', message='Permintaan tidak valid. Silakan periksa data Anda.',
                            errors=form.errors),
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            return Response(custom_response(status='error', message='Pengguna tidak ditemukan'),
                            status=status.HTTP_404_NOT_FOUND)

        form = UserProfileUpdateForm(data, user=user)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
            
            serializer = UserSerializer(user)
            data = serializer.data
            return Response(custom_response(status='success', message='Berhasil ubah data profil', data=data),
                        status=status.HTTP_200_OK)
        
        return Response(
            custom_response(status='error', message='Permintaan tidak valid. Silakan periksa data Anda.',
                            errors=form.errors),
            status=status.HTTP_400_BAD_REQUEST
        )
        
        
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationDefault
    
    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('-updated_at', '-created_at')
        search = self.request.GET.get('search', None)
    
        if search:
            queryset = queryset.filter(
                first_name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                username__icontains=search
            )
            
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan daftar pengguna.",
            data=response.data,
            status="success"
        ), status=response.status_code)


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            return Response(custom_response(status='error', message='Pengguna tidak ditemukan'),
                            status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        data = serializer.data
        return Response(custom_response(status='success', message='Berhasil mendapatkan data profil', data=data),
                        status=status.HTTP_200_OK)


class UserDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def get(self, request, id):
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response(custom_response(status='error', message='Pengguna tidak ditemukan'),
                            status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        data = serializer.data
        return Response(custom_response(status='success', message='Berhasil mendapatkan detail user', data=data),
                        status=status.HTTP_200_OK)


class UserDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = CustomUser.objects.all()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data Pengguna",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    

class UserUsernameView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(custom_response(status='error', message='User tidak ditemukan'),
                            status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        data = serializer.data
        return Response(custom_response(status='success', 
                                        message='Berhasil mendapatkan detail user', data=data),
                        status=status.HTTP_200_OK)