from django import forms
from django.contrib.auth import get_user_model
from utils.choices import UserRole, RegisteredVia
from utils import generate_username_from_email
from penjualan.models import Pabrik


class PasswordResetForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Password"
    )
    repassword = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Repeat Password"
    )
    otp = forms.CharField(
        max_length=8,
        label="Token"
    )
    otp_token = forms.CharField(
        max_length=64,
        label="Token"
    )
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        repassword = cleaned_data.get("repassword")
        if password and repassword and password != repassword:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class RegisterRequestForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Name"
    )
    email = forms.EmailField(
        max_length=254,
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Password"
    )
    repassword = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Repeat Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if email and get_user_model().objects.filter(email=email).exists():
            self.add_error("email", "Email is already registered.")
        
        password = cleaned_data.get("password")
        repassword = cleaned_data.get("repassword")
        if password and repassword and password != repassword:
            self.add_error("password", "Passwords do not match.")
        return cleaned_data
    

class RegisterConfirmForm(RegisterRequestForm):
    otp = forms.CharField(
        max_length=8,
        label="Token"
    )
    otp_token = forms.CharField(
        max_length=64,
        label="Token"
    )

    def create_user(self, registered_via=RegisteredVia.ANDROID):
        User = get_user_model()
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            username=generate_username_from_email(cleaned_data.get("email")),
            email=cleaned_data.get("email"),
            password=cleaned_data.get("password"),
            first_name=cleaned_data.get("name"),
            registered_via=registered_via   
        )
        return user


class ChangePasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="New Password"
    )
    re_new_password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Repeat New Password"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        new_password = cleaned_data.get("new_password")
        re_new_password = cleaned_data.get("re_new_password")

        # Pastikan password lama benar
        if password and not self.user.check_password(password):
            self.add_error("password", "Kata sandi lama salah.")

        # Pastikan password baru sama
        if new_password and re_new_password and new_password != re_new_password:
            self.add_error("new_password", "Kata sandi baru tidak cocok.")

        return cleaned_data
    
    def save(self):
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            self.user.set_password(new_password)
            self.user.save()
        return self.user
    

class UserCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Name"
    )
    email = forms.EmailField(
        max_length=254,
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Password"
    )
    repassword = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Repeat Password"
    )
    roles = forms.MultipleChoiceField(
        choices=UserRole.choices,
        label="Roles"
    )
    is_active = forms.BooleanField(
        required=True,
        initial=True,
        label="Is Active"
    )
    ketua_kelompok_tani = forms.CharField(
        max_length=100,
        required=False,
        label="Ketua Kelompok Tani"
    )
    pabrik = forms.IntegerField(
        required=False,
        label="Pabrik"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        repassword = cleaned_data.get("repassword")

        User = get_user_model()
        if email and User.objects.filter(email=email).exists():
            self.add_error("email", "Email sudah terdaftar.")
        if username and User.objects.filter(username=username).exists():
            self.add_error("username", "Username username sudah digunakan")
        if password and repassword and password != repassword:
            self.add_error("password", "Kata sandi tidak cocok.")
        if UserRole.KETUA_KELOMPOK_TANI in cleaned_data.get("roles", []) and not cleaned_data.get("ketua_kelompok_tani"):
            self.add_error("ketua_kelompok_tani", "Field ini wajib diisi jika peran 'Ketua Kelompok Tani' dipilih.")
        pabrik_id = cleaned_data.get("pabrik")
        if UserRole.MITRA_PABRIK in cleaned_data.get("roles", []) and not pabrik_id:
            self.add_error("pabrik", "Field ini wajib diisi jika peran 'Mitra Pabrik' dipilih.")
        elif pabrik_id and not Pabrik.objects.filter(pk=pabrik_id).exists():
            self.add_error("pabrik", "Pabrik dengan ID tersebut tidak ditemukan.")
        return cleaned_data
    
    def save(self):
        User = get_user_model()
        cleaned_data = self.cleaned_data
        
        if UserRole.ADMIN in cleaned_data["roles"]:
            is_superuser = True
            is_staff = True
        else:
            is_superuser = False
            is_staff = False
            
        user = User.objects.create_user(
            username=generate_username_from_email(cleaned_data.get("email")),
            email=cleaned_data.get("email"),
            password=cleaned_data.get("password"),
            first_name=cleaned_data.get("name"),
            roles=cleaned_data.get("roles"),
            is_active=cleaned_data.get("is_active"),
            is_staff=is_staff,
            is_superuser=is_superuser,
            registered_via=RegisteredVia.WEB_ADMIN,
            ketua_kelompok_tani=cleaned_data.get("ketua_kelompok_tani"),
            pabrik_id=cleaned_data.get("pabrik")
        )
        return user
    

class UserUpdateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Name"
    )
    email = forms.EmailField(
        max_length=254,
        label="Email"
    )
    username = forms.CharField(
        max_length=150,
        label="Username"
    )
    roles = forms.MultipleChoiceField(
        choices=UserRole.choices,
        label="Roles"
    )
    ketua_kelompok_tani = forms.CharField(
        max_length=100,
        required=False,
        label="Ketua Kelompok Tani"
    )
    pabrik = forms.IntegerField(
        required=False,
        label="Pabrik"
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Is Active"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")

        User = get_user_model()
        users = User.objects.exclude(pk=self.user.pk)
        if email and users.filter(email=email).exists():
            self.add_error("email", "Email sudah terdaftar.")
        if email and users.filter(username=username).exists():
            self.add_error("username", "Username sudah ada.")
        if UserRole.KETUA_KELOMPOK_TANI in cleaned_data.get("roles", []) and not cleaned_data.get("ketua_kelompok_tani"):
            self.add_error("ketua_kelompok_tani", "Field ini wajib diisi jika peran 'Ketua Kelompok Tani' dipilih.")
        pabrik_id = cleaned_data.get("pabrik")
        if UserRole.MITRA_PABRIK in cleaned_data.get("roles", []) and not pabrik_id:
            self.add_error("pabrik", "Field ini wajib diisi jika peran 'Mitra Pabrik' dipilih.")
        elif pabrik_id and not Pabrik.objects.filter(pk=pabrik_id).exists():
            self.add_error("pabrik", "Pabrik dengan ID tersebut tidak ditemukan.")
        return cleaned_data
    
    def save(self):
        cleaned_data = self.cleaned_data
        self.user.email=cleaned_data.get("email")
        self.user.username=cleaned_data.get("username")
        self.user.first_name=cleaned_data.get("name")
        self.user.roles=cleaned_data.get("roles")
        self.user.is_active=cleaned_data.get("is_active")
        self.user.ketua_kelompok_tani = cleaned_data.get("ketua_kelompok_tani")
        self.user.pabrik_id = cleaned_data.get("pabrik")
        if UserRole.ADMIN in cleaned_data["roles"]:
            self.user.is_superuser = True
            self.user.is_staff = True
        else:
            self.user.is_superuser = False
            self.user.is_staff = False
        self.user.save()
        return self.user


class UserProfileUpdateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Name"
    )
    email = forms.EmailField(
        max_length=254,
        label="Email"
    )
    username = forms.CharField(
        max_length=150,
        label="Username"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")

        User = get_user_model()
        users = User.objects.exclude(pk=self.user.pk)
        if email and users.filter(email=email).exists():
            self.add_error("email", "Email sudah terdaftar.")
        if email and users.filter(username=username).exists():
            self.add_error("username", "Username sudah ada.")
        return cleaned_data
    
    def save(self):
        cleaned_data = self.cleaned_data
        self.user.email=cleaned_data.get("email")
        self.user.username=cleaned_data.get("username")
        self.user.first_name=cleaned_data.get("name")
        self.user.save()
        return self.user
