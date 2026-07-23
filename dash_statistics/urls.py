from django.urls import path
from . import views
from petani import views as petani_views
from kebun import views as kebun_views
from penjualan import views as penjualan_views

app_name = 'dash_statistics'

urlpatterns = [
    path('petani/gender/', petani_views.PetaniGenderStatisticView.as_view(), name='petani-gender'),
    path('petani/dokumen/', petani_views.PetaniDokumenStatisticView.as_view(), name='petani-dokumen'),
    path('kebun/dokumen/', kebun_views.KebunDokumenStatisticView.as_view(), name='kebun-dokumen'),
    path('kebun/dokumen/v2/', views.KebunDokumenStatisticV2View.as_view(), name='kebun-dokumen-v2'),
    
    # Sankey Diagram
    path('sankey-diagram/', penjualan_views.SankeyDiagramAPIView.as_view(), name='sankey-diagram'),
    
    # Bar Chart
    path('bar-chart/total-penjualan/', penjualan_views.TotalPenjualanBarChartAPIView.as_view(), 
         name='bar-chart-total-penjualan'),
    path('bar-chart/berat-timbangan/', penjualan_views.BeratTimbanganBarChartAPIView.as_view(), 
         name='bar-chart-berat-timbangan'),
    path('bar-chart/jumlah-tandan/', penjualan_views.JumlahTandanBarChartAPIView.as_view(), 
         name='bar-chart-jumlah-tandan'),
    
    # Donut Chart
    path('donut-chart/berat-timbangan-pabrik/', penjualan_views.BeratTimbanganPabrikDonutChartAPIView.as_view(), 
         name='donut-chart-berat-timbangan-pabrik'),
    
    # Sidebar Statistics
    path('sidebar-statistics/', views.SidebarStatisticView.as_view(), name='sidebar-statistics'),

]