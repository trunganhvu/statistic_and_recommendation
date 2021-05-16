from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from mainApp.models import Units, Generations, Majors, Courses, Semesters, Years, Profiles, Major_Course
from mainApp.models import CustomUser
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.template.response import TemplateResponse
from json import dumps
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog

@login_required(login_url='/login/')
def suggestioncourse_page(request):
    """
    Hiện thị trang gợi ý môn học
    """
    if checkInUrl(request, 'suggestioncourse') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        profiles = []
        isStudent = False
        if unitRole == 0:
            profiles = Profiles.objects.all().values('profileID', 'firstName', 'lastName', 'MSSV').order_by('-MSSV')
        elif unitRole is None:
            profiles = Profiles.objects.filter(user_id=request.user.id).values('profileID', 'firstName', 'lastName', 'MSSV')
            isStudent = True
        else:
            profiles = Profiles.objects.filter(major__unit_id=unitRole).values('profileID', 'firstName', 'lastName', 'MSSV').order_by('-MSSV')
        context = {
            'profiles': profiles,
            'isStudent': isStudent,
        }
        createLog(request, 'VIEW - Gợi ý môn học', '')
    return TemplateResponse(request, 'adminuet/suggestioncourse.html', context=context)