from django.urls import path
from . import views

app_name = 'kebun'

urlpatterns = [
    path('list/', views.KebunListView.as_view(), name='kebun-list'),
    path('list/download/', views.KebunDownloadListView.as_view(), name='kebun-list-download'),
    path('detail/<int:pk>/', views.KebunDetailView.as_view(), name='kebun-detail'),
    path('create/', views.KebunCreateView.as_view(), name='kebun-create'),
    path('update/<int:pk>/', views.KebunUpdateView.as_view(), name='kebun-update'),
    path('delete/<int:pk>/', views.KebunDeleteView.as_view(), name='kebun-delete'),
    path('lampiran/create/', views.LampiranKebunCreateView.as_view(), name='lampiran-kebun-create'),
    path('lampiran/update/<int:pk>/', views.LampiranKebunUpdateView.as_view(), name='lampiran-kebun-update'),
    path('lampiran/detail/<int:pk>/', views.LampiranKebunDetailView.as_view(), name='lampiran-kebun-detail'),
    path('statistik/dokumen/', views.KebunDokumenStatisticView.as_view(), name='kebun-dokumen-statistik'),
    path('peta/create-update/<int:pk>/', views.KebunGeomCreateUpdateView.as_view(), name='kebun-peta-create-update'),
    path('peta/upload-shapefile/<int:pk>/', views.KebunGeomUploadShapefileView.as_view(), name='kebun-peta-upload-shapefile'),
    path('peta/download/<int:pk>/', views.KebunDownloadSHPView.as_view(), name='kebun-peta-download'),
    path('deforestation-analysis/<int:pk>/', views.KebunDeforestationAnalysisView.as_view(),
         name='kebun-deforestation-analysis'),
    path('deforestation-status/<int:pk>/', views.KebunDeforestationStatusView.as_view(),
         name='kebun-deforestation-status'),
    path('deforestation-properties/<int:pk>/', views.KebunDeforestationPropertiesView.as_view(),
         name='kebun-deforestation-properties'),
]