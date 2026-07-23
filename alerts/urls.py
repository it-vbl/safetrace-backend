from django.urls import path
from . import views

app_name = 'alert'

urlpatterns = [
    path('deforestation/', views.AlertDeforestationListView.as_view(), name='deforestation-alerts'),
]