from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages

from mainApp.forms import CoursesForm
from mainApp.models import Courses, Units, Transcript, CustomUser, Profiles
from mainApp.serializers.cousersserializer import CoursesSerializer
from mainApp.serializers.unitserializer import UnitSerializer
from mainApp.viewapi.logs import createLog
import math
import datetime
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect

@login_required(login_url='/login/')
def viewlearningoutcome(request):
    """
    Hiển thị trang xem điểm sinh viên
    """
    if checkInUrl(request, 'viewlearningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        userId = request.user.id
        profileIdResult = Profiles.objects.filter(user_id=userId).values('profileID')
        profileId = 0
        for id in profileIdResult:
            profileId = id['profileID']
        transcripts = Transcript.objects.filter(student=profileId) #.prefetch_related('course', 'semester')
        arraySemesterID = []
        arraySemesterName = []
        for transcript in transcripts:
            if transcript.semester.semesterID not in arraySemesterID:
                arraySemesterID.append(transcript.semester.semesterID)
                arraySemesterName.append(transcript.semester.semesterName)

        transcriptsResult = {}
        for id, name in zip(arraySemesterID, arraySemesterName):
            arrTranscriptInSemester = []
            for transcript in transcripts:
                dictTranscriptInSemester = {}
                if transcript.semester.semesterID == id:
                    dictTranscriptInSemester['courseCode'] = transcript.course.courseCode
                    dictTranscriptInSemester['courseName'] = transcript.course.courseName 
                    dictTranscriptInSemester['grade'] = transcript.grade
                    arrTranscriptInSemester.append(dictTranscriptInSemester)
            
            transcriptsResult[name] = arrTranscriptInSemester 
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return TemplateResponse(request, 'adminuet/transcriptpersonal.html', {'transcriptsResult': transcriptsResult, 'transcripts': transcripts})

@login_required(login_url='/login/')
def viewProfile(request):
    """
    Hiển thị trang xem thông tin profile
    """
    userId = request.user.id
    
    username = ''
    lastName = ''
    firstName = ''
    MSSV = ''
    email = ''
    birthday = ''#datetime.date.today()
    group = ''
    major = ''
    generation = ''
    if request.method == 'GET':
        user = CustomUser.objects.filter(pk=userId)
        for u in user:
            username = u.username
        profileUser = Profiles.objects.filter(user=userId)
        for p in profileUser:
            lastName = p.lastName
            firstName = p.firstName
            MSSV = p.MSSV
            email = p.email
            birthday = p.birthday
            group = p.group.groupName
            major = p.major.majorName
            generation = p.group.generation.generationName
            birthday = str(birthday)
        context = {
            'username': username,
            'lastName': lastName,
            'firstName': firstName,
            'MSSV': MSSV,
            'email': email,
            'birthday': birthday,
            'group': group,
            'major': major,
            'generation': generation,
        }
        return TemplateResponse(request, 'adminuet/profile.html', context=context)
    else:
        try:
            lastName = request.POST.get('lastName')
            firstName = request.POST.get('firstName')
            email = request.POST.get('email')
            birthday = request.POST.get('birthday')
            checkExistProfile = Profiles.objects.filter(user=userId).exists()
            # Update
            if checkExistProfile:
                Profiles.objects.filter(user=userId).update(lastName=lastName, firstName=firstName, email=email, birthday=birthday)
                messages.success(request, "Cập nhật thành công.")
            else: # Create
                print(checkExistProfile)
        except Exception as error:
            print(error)
            messages.error(request, "Thao tác thất bại.")
        return redirect('/adminuet/profile/')