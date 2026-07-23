from django.urls import path
from referensi import views

app_name = 'referensi'

urlpatterns = [
    path('jenis-kelamin/', views.JenisKelaminView.as_view(), name='jenis-kelamin'),
    path('status-perkawinan/', views.StatusPerkawinanView.as_view(), name='status-perkawinan'),
    path('request-otp-via/', views.RequestOTPViaView.as_view(), name='request-otp-via'),
    path('user-roles/', views.UserRoleView.as_view(), name='user-roles'),
    path('jenis-legalitas/', views.JenisLegalitasView.as_view(), name='jenis-legalitas'),
    path('registered-via/', views.RegisteredViaView.as_view(), name='registered-via'),
    path('pendidikan-terakhir/', views.PendidikanTerakhirView.as_view(), name='pendidikan-terakhir'),
    path('sumber-kontak/', views.SumberKontakView.as_view(), name='sumber-kontak'),
    path('penerima-boardcast/', views.PenerimaBoardcastView.as_view(), name='penerima-boardcast'),
    path('status-pekerja/', views.StatusPekerjaView.as_view(), name='status-pekerja'),
    path('whisp-status/', views.WHISPStatusView.as_view(), name='whisp-status'),
    path('pilihan-bulan/', views.PilihanBulanView.as_view(), name='pilihan-bulan'),
    path('deforestation-alert-type/', views.DeforestationSourceTypeView.as_view(), name='deforestation-alert-type'),
    path('status-keanggotaan/', views.StatusKeanggotaanView.as_view(), name='status-keanggotaan'),
    path('status-lahan/', views.StatusLahanView.as_view(), name='status-lahan'),
    path('pola-tanam/', views.PolaTanamView.as_view(), name='pola-tanam'),
    path('asal-benih/', views.AsalBenihView.as_view(), name='asal-benih'),
    path('jenis-lahan/', views.JenisLahanView.as_view(), name='jenis-lahan'),
    path('jenis-pupuk/', views.JenisPupukView.as_view(), name='jenis-pupuk'),
    path('jenis-pekerjaan/', views.JenisPekerjaanView.as_view(), name='jenis-pekerjaan'),
    path('jenis-apd/', views.JenisAPDView.as_view(), name='jenis-apd'),
    path('komoditas/', views.KomoditasKelembagaanView.as_view(), name='komoditas-kelembagaan'),
    path('status-stdb/', views.StatusSTDBView.as_view(), name='status-stdb'),
]
