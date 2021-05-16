from django.urls import path
from . import views
from . import adminviews
from .viewapi import showviewlearningoutcomeview

urlpatterns = [
    # ---------------- Url đăng nhập ----------------
    path('login/', adminviews.user_login2, name='login'),

    # ---------------- Url đăng xuất ----------------
    path('logout/', adminviews.user_logout, name='logout'),

    # ----------------Các url về  hồ sơ ----------------
    path('info-first/', adminviews.first_form, name='info-first'),
    path('info-second/', adminviews.second_form, name='info-second'),
    path('info-third/', adminviews.third_form, name='info-third'),

]
