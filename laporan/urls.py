from django.urls import path
from . import views

app_name = 'laporan'

urlpatterns = [
    path('statistik/create/', views.LaporanStatistikCreateView.as_view(), name='statistik-create'),
    path('statistik/', views.LaporanStatistikListView.as_view(), name='statistik-list'),
    path('statistik/<int:pk>/', views.LaporanStatistikDetailView.as_view(), name='statistik-detail'),
    path('statistik/<int:pk>/download/', views.LaporanStatistikDownloadView.as_view(), name='statistik-download'),
    path('statistik/<int:pk>/delete/', views.LaporanStatistikDeleteView.as_view(), name='statistik-delete'),
    path('stdb/excel/', views.LaporanSTDBExcelView.as_view(), name='stdb-excel'),
    path('statistik-kelompok/excel/', views.LaporanStatistikKelompokExcelView.as_view(), name='statistik-kelompok-excel'),
    path('petani/<int:id_petani>/', views.LaporanPetaniView.as_view(), name='petani'),
]
