from django.urls import path
from referensi import wilayah_views as views

app_name = 'wilayah'

urlpatterns = [
    path('provinsi/', views.WilayahProvinsiView.as_view(), name='provinsi-list'),
    path('provinsi/detail/<int:pk>/', views.WilayahProvinsiDetailView.as_view(), name='provinsi-detail'),
    path('kabupaten/<int:provinsi_id>/', views.WilayahKabupatenView.as_view(), name='kabupaten-list'),
    path('kabupaten/detail/<int:pk>/', views.WilayahKabupatenDetailView.as_view(), name='kabupaten-detail'),
    path('kecamatan/<int:kabupaten_id>/', views.WilayahKecamatanView.as_view(), name='kecamatan-list'),
    path('kecamatan/detail/<int:pk>/', views.WilayahKecamatanDetailView.as_view(), name='kecamatan-detail'),
    path('desa/<int:kecamatan_id>/', views.WilayahDesaView.as_view(), name='desa-list'),
    path('desa/detail/<int:pk>/', views.WilayahDesaDetailView.as_view(), name='desa-detail'),
    path('kecamatan/sanggau/', views.WilayahKecamatanSanggauView.as_view(), name='kecamatan-sanggau'),
]
