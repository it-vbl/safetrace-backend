from django.urls import path
from layer_static.views import (
    preview_arcgis_server, LayerStaticView, LayerStaticListView, PetaStatisCreateView, PetaStatisListView,
    PetaStatisUpdateView, PetaStatisDeleteView, PetaStatisDetailView
)

app_name = 'layer-static'

urlpatterns = [
    path('preview-arcgis/', preview_arcgis_server, name='preview-arcgis'),
    path('detail/<slug:slug>/', LayerStaticView.as_view(), name='layer-static-detail'),
    path('list/', LayerStaticListView.as_view(), name='layer-static-list'),
    path('peta/list/', PetaStatisListView.as_view(), name='layer-static-peta-list'),
    path('peta/create/', PetaStatisCreateView.as_view(), name='layer-static-peta-create'),
    path('peta/detail/<int:pk>/', PetaStatisDetailView.as_view(), name='layer-static-peta-detail'),
    path('peta/update/<int:pk>/', PetaStatisUpdateView.as_view(), name='layer-static-peta-update'),
    path('peta/delete/<int:pk>/', PetaStatisDeleteView.as_view(), name='layer-static-peta-delete')
]
