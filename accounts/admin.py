from django.contrib import admin
from .models import CustomUser, RequestOTP
from django.contrib.auth.admin import UserAdmin


@admin.register(RequestOTP)
class RequestOTPAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'via', 'otp', 'token', 'is_used', 'expiration_time')
    search_fields = ('user__username', 'otp', 'token')
    list_filter = ('is_used', 'via')
    readonly_fields = ('created_at', 'updated_at', 'expiration_time')


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'roles')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info',
         {'fields': ('first_name', 'last_name', 'email', 'roles', 
                     'email_is_valid')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    
admin.site.register(CustomUser, CustomUserAdmin)