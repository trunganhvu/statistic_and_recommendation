from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.models import Profiles, Generations, Courses, Majors, TimeLinePredicted
from rest_framework.decorators import api_view
from rest_framework.response import Response
from mainApp.serializers.timelinepredictedserializer import TimeLinePredictedSerializer
from datetime import datetime
from mainApp.viewapi.logs import createLog
from rest_framework import status

@login_required(login_url='/login/')
def scoreforecast_page(request):
    """
    Hiển thị trang dự báo điểm
    """
    context = None
    if checkInUrl(request, 'scoreforecast') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        profiles = []
        isStudent = False
        generations = None
        majors = None
        if unitRole == 0:
            profiles = Profiles.objects.all().values('profileID', 'firstName', 'lastName', 'MSSV').order_by('-MSSV')
            generations = Generations.objects.order_by('unit').all()
            courses = Courses.objects.order_by('unit').all()
            majors = Majors.objects.order_by('unit').all()
        elif unitRole is None:
            profiles = Profiles.objects.filter(user_id=request.user.id)#.values('profileID', 'firstName', 'lastName', 'MSSV')
            isStudent = True
            unitId = 0
            for pro in profiles:
                unitId = pro.major.unit.unitID
            courses = Courses.objects.filter(unit=unitId).order_by('courseCode').all()
        else:
            profiles = Profiles.objects.filter(major__unit_id=unitRole).values('profileID', 'firstName', 'lastName', 'MSSV').order_by('-MSSV')
            generations = Generations.objects.filter(unit=unitRole).all()
            courses = Courses.objects.filter(unit=unitRole).order_by('courseCode').all()
            majors = Majors.objects.filter(unit=unitRole).order_by('unit').all()
        context = {
            'profiles': profiles,
            'isStudent': isStudent,
            'generations': generations,
            'courses': courses,
            'majors': majors,
        }

    return TemplateResponse(request, 'adminuet/scoreforecast.html', context=context)

@login_required(login_url='/login/')
def scoreforecast_generation_page(request):
    """
    Hiển thị trang tính dự báo điểm
    """
    context = None
    if checkInUrl(request, 'scoreforecast') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            generations = Generations.objects.order_by('unit').all()
            majors = Majors.objects.order_by('unit').all()
        else:
            generations = Generations.objects.filter(unit=unitRole).all()
            majors = Majors.objects.filter(unit=unitRole).order_by('unit').all()
        context = {
            'generations': generations,
            'majors': majors,
        }
        # createLog(request, 'VIEW - Tính dự đoán theo khóa', '')
        return TemplateResponse(request, 'adminuet/scoreforecastgeneration.html', context=context)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def time_scoreforecast_generation_page(request, major, generation):
    if request.method == 'GET':
        timeline = TimeLinePredicted.objects.filter(major=major, generation=generation).order_by('-timeLineID')[:1]
        timeLinePredictedSerializer = TimeLinePredictedSerializer(timeline,  many = True)
        data = {
            'data': timeLinePredictedSerializer.data,
        }
        return Response(data)
    else:
        try:
            isExistMajor = Majors.objects.filter(pk=major).exists()
            isExistGeneration = Generations.objects.filter(pk=generation).exists()
            if isExistMajor and isExistGeneration:
                print("have")
                # createLog(request, 'UPDATE - Tính dự đoán theo khóa', '')
                timeline = TimeLinePredicted(major_id=major, generation_id=generation, time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                timeline.save()
                return Response(202)
            else:
                print("not have")
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response(404)
