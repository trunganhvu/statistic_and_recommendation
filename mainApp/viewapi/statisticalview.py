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
def distribute_transcript(request):
    """
    Hiển thị trang thống kê phổ điểm
    """
    if checkInUrl(request, 'statistical') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            units = Units.objects.all()
        elif unitRole is None:
            # units = Profiles.objects.filter(user=request.user).select_related("major__unit")
            unitIdQuery = Profiles.objects.filter(user=request.user)
            unitId = 1
            for i in unitIdQuery:
                unitId = i.major.unit.unitID
            units = Units.objects.filter(unitID=unitId).all()
        else:
            units = Units.objects.filter(pk=unitRole)
        semesters = Semesters.objects.all()
        context = {
            'units': units,
            'semesters': semesters,
        }
        createLog(request, 'VIEW - Thống kê', 'Phổ điểm')
        return TemplateResponse(request, 'adminuet/statistical.html', context=context)

@login_required(login_url='/login/')
def course_avg_transcript(request):
    """
    Hiển thị trang thông kê điểm trung bình theo môn học
    """
    if checkInUrl(request, 'course-avg') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            units = Units.objects.all()
        elif unitRole is None:
            # units = Profiles.objects.filter(user=request.user).select_related("major__unit")
            unitIdQuery = Profiles.objects.filter(user=request.user)
            unitId = 1
            for i in unitIdQuery:
                unitId = i.major.unit.unitID
            units = Units.objects.filter(unitID=unitId).all()
        else:
            units = Units.objects.filter(pk=unitRole)

        context = {
            'units': units,
        }
        createLog(request, 'VIEW - Thống kê', 'Điểm trung bình')
        return TemplateResponse(request, 'adminuet/courseavg.html', context=context)

@login_required(login_url='/login/')
def gpa_generation(request):
    """
    Hiển thị trang thống kê GPA theo khóa
    """
    if checkInUrl(request, 'statistical-gpa') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            units = Units.objects.all()
        elif unitRole is None:
            # units = Profiles.objects.filter(user=request.user).select_related("major__unit")
            unitIdQuery = Profiles.objects.filter(user=request.user)
            unitId = 1
            for i in unitIdQuery:
                unitId = i.major.unit.unitID
            units = Units.objects.filter(unitID=unitId).all()
        else:
            units = Units.objects.filter(pk=unitRole)

        majors = Majors.objects.all()
        generations = Generations.objects.all().order_by('-generationName')
        context = {
            'units': units,
            'generations': generations,
            'majors': majors,
        }
        createLog(request, 'VIEW - Thống kê', 'GPA')
        return TemplateResponse(request, 'adminuet/gpageneration.html', context=context)
        
@login_required(login_url='/login/')
def gpa_student(request):
    """
    Hiển thị trang thống kê theo GPA sinh viên
    """
    if checkInUrl(request, 'statistical-gpa-student') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            profiles = Profiles.objects.all().select_related('user').order_by('-MSSV')
        elif unitRole is None:
            profiles = Profiles.objects.filter(user_id=request.user.id).select_related('user')
        else:
            profiles = Profiles.objects.filter(major__unit_id=unitRole).select_related('user').order_by('-MSSV')
        # else:
        #     roleId = request.user.role_id

        # print(profiles)
        semesters = Semesters.objects.all()
        dict_semesters = {}
        for semester in semesters:
            dict_semesters[semester.semesterID] = semester.semesterName  
        context = {
            'profiles': profiles,
            'semesters': dumps(dict_semesters),
        }
        createLog(request, 'VIEW - Thống kê', 'GPA Sinh viên')
        return TemplateResponse(request, 'adminuet/gpastudent.html', context=context)