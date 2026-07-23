# models.py
import random, string, uuid
from datetime import timedelta, datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from utils.fields import ChoiceArrayField
from utils.choices import UserRole, RequestOTPVia, RegisteredVia


class CustomUser(AbstractUser):
    email_is_valid = models.BooleanField(default=False)
    roles = ChoiceArrayField(
        models.CharField(max_length=2, choices=UserRole.choices),
        blank=True,
        default=list
    )
    registered_via = models.CharField(max_length=2, choices=RegisteredVia.choices, default=RegisteredVia.WEB_ADMIN)
    ketua_kelompok_tani = models.CharField(max_length=100, blank=True, null=True)
    pabrik = models.ForeignKey('penjualan.Pabrik', on_delete=models.SET_NULL, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('updated_at', 'created_at')
        
    def __str__(self) -> str:
        return super().__str__()

    def get_roles_display(self):
        return ', '.join([role.label for role in UserRole if role.value in self.roles])


class RequestOTP(models.Model):
    identifier = models.CharField(max_length=30)
    via = models.CharField(max_length=2, choices=RequestOTPVia.choices)
    otp = models.CharField(max_length=6)
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_time = models.DateTimeField()
    
    def __str__(self) -> str:
        return f"OTP for {self.identifier} - Token: {self.otp}"
    
    @classmethod
    def create_otp(cls, identifier, via=RequestOTPVia.EMAIL):
        otp = ''.join(random.choices(string.digits, k=6))
        token = uuid.uuid4().hex
        expiration_time = datetime.now() + timedelta(minutes=10)
        obj = cls.objects.create(identifier=identifier, otp=otp, via=via, token=token, expiration_time=expiration_time)
        return obj
