from django.urls import path
from . import views

app_name = 'penjualan'

urlpatterns = [
    # Angkutan
    path('angkutan/list/', views.AngkutanListView.as_view(), name='angkutan-list'),
    path('angkutan/list/download/', views.AngkutanDownloadListView.as_view(), name='angkutan-list-download'),
    path('angkutan/detail/<int:pk>/', views.AngkutanDetailView.as_view(), name='angkutan-detail'),
    path('pabrik/detail-by-angkutan/<int:pk>/', views.PabrikDetailByAngkutanView.as_view(), 
         name='pabrik-detail-by-angkutan'),
    path('angkutan/create/', views.AngkutanCreateView.as_view(), name='angkutan-create'),
    path('angkutan/update/<int:pk>/', views.AngkutanUpdateView.as_view(), name='angkutan-update'),
    path('angkutan/delete/<int:pk>/', views.AngkutanDeleteView.as_view(), name='angkutan-delete'),
    path('angkutan/update/<int:pk>/', views.AngkutanUpdateView.as_view(), name='angkutan-update'),
    path('angkutan/update-pabrik/<int:pk>/', views.AngkutanPabrikUpdateView.as_view(), name='angkutan-update-pabrik'),

     # Lampiran Penjualan
     path('lampiran/list/', views.LampiranListView.as_view(), name='lampiran-list'),
     path('lampiran/detail/<int:pk>/', views.LampiranDetailView.as_view(), name='lampiran-detail'),
     path('lampiran/create/', views.LampiranCreateView.as_view(), name='lampiran-create'),
     path('lampiran/update/<int:pk>/', views.LampiranUpdateView.as_view(), name='lampiran-update'),
     path('lampiran/delete/<int:pk>/', views.LampiranDeleteView.as_view(), name='lampiran-delete'),
    
    # Kelompok Penyetor
    path('kelompok-penyetor/list/', views.KelompokPenyetorListView.as_view(), name='kelompok-penyetor-list'),
    path('kelompok-penyetor/detail/<int:pk>/', views.KelompokPenyetorDetailView.as_view(), name='kelompok-penyetor-detail'),
    path('kelompok-penyetor/bulk-create/', views.KelompokPenyetorBulkCreateView.as_view(), name='kelompok-penyetor-bulk-create'),
    path('kelompok-penyetor/update/<int:pk>/', views.KelompokPenyetorUpdateView.as_view(), name='kelompok-penyetor-update'),
    path('kelompok-penyetor/delete/<int:pk>/', views.KelompokPenyetorDeleteView.as_view(), name='kelompok-penyetor-delete'),
    
    # Pabrik
    path('pabrik/list/', views.PabrikListView.as_view(), name='pabrik-list'),
    path('pabrik/detail/<int:pk>/', views.PabrikDetailView.as_view(), name='pabrik-detail'),
    path('pabrik/create/', views.PabrikCreateView.as_view(), name='pabrik-create'),
    path('pabrik/update/<int:pk>/', views.PabrikUpdateView.as_view(), name='pabrik-update'),
    path('pabrik/delete/<int:pk>/', views.PabrikDeleteView.as_view(), name='pabrik-delete'),
    
    # Sankey Diagram
    path('sankey-diagram/', views.SankeyDiagramAPIView.as_view(), name='sankey-diagram'),
    path('sankey-diagram/download/', views.SankeyDiagramDownloadCSVView.as_view(), name='sankey-diagram-download'),
    
    # Bar Chart
    path('bar-chart/total-penjualan/', views.TotalPenjualanBarChartAPIView.as_view(), 
         name='bar-chart-total-penjualan'),
    path('bar-chart/berat-timbangan/', views.BeratTimbanganBarChartAPIView.as_view(), 
         name='bar-chart-berat-timbangan'),
    path('bar-chart/jumlah-tandan/', views.JumlahTandanBarChartAPIView.as_view(), 
         name='bar-chart-jumlah-tandan'),
    
    # Donut Chart
    path('donut-chart/berat-timbangan-pabrik/', views.BeratTimbanganPabrikDonutChartAPIView.as_view(), 
         name='donut-chart-berat-timbangan-pabrik'),
]
