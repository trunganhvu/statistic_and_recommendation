"""    source venv/bin/activate

project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import TemplateView

from django.conf.urls import url
from django.views.static import serve

from django.conf import settings
from django.conf.urls.static import static

from project import settings
from statistic import urls as st_urls
from recommendation import urls as rec_urls
from . import views

from django.conf.urls import (handler400, handler403, handler404, handler500)


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', TemplateView.as_view(template_name="home.html"), name = 'trangchu'),
    path('', views.home_page, name = "trangchu"),
    path('', include('mainApp.urls')),
    path('adminuet/', include('mainApp.adminurls')),
    path('statistic/', include(st_urls)),
    path('recommend/', include(rec_urls)),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
handler400 = 'project.views.NotFoundPage'
handler403 = 'project.views.NotFoundPage'
handler404 = 'project.views.NotFoundPage'
# handler500 = 'project.views.BadRequestPage'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)