from django.urls import path
from . import views

app_name = 'petani'

urlpatterns = [
    path('list/', views.PetaniListView.as_view(), name='petani-list'),
    path('list/download/', views.PetaniListDownloadView.as_view(), name='petani-list-download'),
    path('list/wa-kontak/', views.PetaniWANotNullView.as_view(), name='petani-list-wa-not-null'),
    path('detail/<int:pk>/', views.PetaniDetailView.as_view(), name='petani-detail'),
    path('create/', views.PetaniCreateView.as_view(), name='petani-create'),
    path('update/<int:pk>/', views.PetaniUpdateView.as_view(), name='petani-update'),
    path('delete/<int:pk>/', views.PetaniDeleteView.as_view(), name='petani-delete'),
    path('lampiran/create/', views.LampiranPetaniCreateView.as_view(), name='lampiran-petani-create'),
    path('lampiran/update/<int:pk>/', views.LampiranPetaniUpdateView.as_view(), name='lampiran-petani-update'),
    path('lampiran/detail/<int:pk>/', views.LampiranPetaniDetailView.as_view(), name='lampiran-petani-detail'),
    path('diklat/list/', views.DiklatListView.as_view(), name='diklat-list'),
    path('diklat/download/', views.DiklatDownloadView.as_view(), name='diklat-download'),
    path('diklat/update/<int:pk>/', views.DiklatUpdateView.as_view(), name='diklat-update'),
    path('diklat/detail/<int:pk>/', views.DiklatDetailView.as_view(), name='diklat-detail'),
    path('diklat/statistik/', views.DiklatStatisticView.as_view(), name='diklat-statistik'),
    path('statistik/gender/', views.PetaniGenderStatisticView.as_view(), name='petani-gender-statistik'),
    path('statistik/dokumen/', views.PetaniDokumenStatisticView.as_view(), name='petani-dokumen-statistik'),
    path('kelompok-tani/list/', views.KelompokTaniListView.as_view(), name='kelompok-list'),
    path('pekerja/list/', views.PekerjaListViewV2.as_view(), name='pekerja-list'),
    path('pekerja/download/', views.PekerjaDownloadView.as_view(), name='pekerja-download'),
    path('pekerja/create/', views.PekerjaCreateView.as_view(), name='pekerja-create'),
    path('pekerja/update/<int:pk>/', views.PekerjaUpdateView.as_view(), name='pekerja-update'),
    path('pekerja/delete/<int:pk>/', views.PekerjaDeleteView.as_view(), name='pekerja-delete'),
    path('pekerja/detail/<int:pk>/', views.PekerjaDetailView.as_view(), name='pekerja-detail'),
    path('pekerja/by-petani/<int:petani_id>/', views.PekerjaByPetaniListView.as_view(), name='pekerja-by-petani'),
    path('pekerja/statistik/', views.PekerjaStatistikView.as_view(), name='pekerja-statistik'),
]