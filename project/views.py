from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.template import loader

# Nếu đã đăng nhập thì hiển thị trang chức năng, nếu chưa hiển thị trang chủ
def home_page(request):
    if request.user.is_authenticated:
        listFunction = request.user.list_function()
        return redirect('adminuet/' + listFunction[0])
    return TemplateResponse(request, 'home.html')
    
def NotFoundPage(request, exception=None):
    return render(request, '404.html')


def BadRequestPage(request):
    return render(request, '404.html')