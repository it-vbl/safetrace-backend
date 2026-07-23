"""safetrace URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from utils.protected_medias import ProtectedMediaView
from utils.protected_medias import ProtectedMediaDownloadView

def trigger_error(request):
    division_by_zero = 1 / 0
    
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('select2/', include('django_select2.urls')),
    path('petani/', include('petani.urls')),
    path('kebun/', include('kebun.urls')),
    path('referensi/', include('referensi.urls')),
    path('wilayah-indonesia/', include('referensi.wilayah_urls')),
    path('gap/', include('gap.urls')),
    path('penjualan/', include('penjualan.urls')),
    path('layer-static/', include('layer_static.urls')),
    path('alerts/', include('alerts.urls')),
    path('statistics/', include('dash_statistics.urls')),
    path('laporan/', include('laporan.urls')),
    path('django-rq/', include('django_rq.urls')),
    path('sentry-debug/', trigger_error),
]


urlpatterns += static(settings.STATIC_URL,
                        document_root=settings.STATIC_ROOT)
# Protected Media URLs
# IMPORTANT: Add this BEFORE any catch-all patterns
urlpatterns += [
    re_path(r'^media/(?P<file_path>.*)$', ProtectedMediaView.as_view(), name='protected_media'),
]
urlpatterns += [
    re_path(r'^media/download/(?P<file_path>.*)$', ProtectedMediaDownloadView.as_view(), 
            name='protected_media_download'),
]