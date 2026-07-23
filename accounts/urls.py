from django.urls import path, include
from accounts.views import (
    CustomTokenObtainPairView, CustomTokenRefreshView, CustomTokenBlacklistView, ForgotPasswordView, 
    ResetPasswordConfirmView, VerifyOTPView, RegisterRequestView, RegisterConfirmView, ChangePasswordView,
    UserCreateView, UserUpdateView, UserListView, UserProfileUpdateView, UserProfileView, UserDetailView, 
    UserUsernameView, UserDeleteView
)


app_name = 'accounts'


urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', CustomTokenBlacklistView.as_view(), name='token_blacklist'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    path('register-request/', RegisterRequestView.as_view(), name='register_request'),
    path('register-confirm/', RegisterConfirmView.as_view(), name='register_confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    path('user/create/', UserCreateView.as_view(), name='user_create'),
    path('user/update/', UserUpdateView.as_view(), name='user_update'),
    path('user/detail/<int:id>/', UserDetailView.as_view(), name='user_detail'),
    path('user/delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
    path('user/list/', UserListView.as_view(), name='user_list'),
    path('user/profile/update/', UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('user/<str:username>/', UserUsernameView.as_view(), name='user_username'),
]
