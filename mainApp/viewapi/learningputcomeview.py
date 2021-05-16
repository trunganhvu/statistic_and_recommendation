from mainApp import models as DBModel
from mainApp.dataprocessing.process_data import DataExtraction
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from mainApp.models import Transcript, Profiles, Courses
from mainApp.serializers.learningoutcomeview import TranscriptSerializer
from mainApp.forms import TranscriptForm
from django.http import HttpResponse
from statistic.views import calculate_student_gpa
import os
import csv
import numpy as np
import pandas as pd
import math
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
from django.contrib import messages


@login_required(login_url='/login/')
def learningoutcomePagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách kết quả học tập có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/learningoutcome.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
def extract_transcript_file(request):
    """
    Extract file điểm csv
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    file_id = request.POST['file_id']
    transcript_file = DBModel.TranscriptFiles.objects.get(pk=file_id)

    extraction = DataExtraction()
    try:
        extraction.loadData(settings.MEDIA_ROOT+'/'+transcript_file.transcript.name)
    except Exception as e:
        print("error: learningoutcome.py line 40: ", e)
        return False
    # format student info DataFrame
    studentInfo = extraction.getStudentInfo()
    studentInfo['birth'] = pd.to_datetime(studentInfo['birth'])
    # studentInfo = studentInfo.loc[:, ['gender', 'birth']].reset_index()
    # studentInfo['group'] = stg
    # studentInfo.columns = ['MSSV', 'gender', 'birthday', 'group']
    # DBModel.create_from_DF(studentInfo, DBModel.Profiles, searching_cols=['MSSV', 'group'])

    # format course info DataFrame
    courseInfo = extraction.getCourse()
    courseInfo.columns = ['courseCode', 'courseName', 'credit']
    courseInfo['unit_id'] = transcript_file.group.generation.unit_id
    # check and create course
    try:
        course_obj_list = DBModel.create_from_DF(courseInfo, DBModel.Courses, searching_cols=['courseCode', 'unit_id'])
        recommend_semester = DBModel.semester_rank(group_id=transcript_file.group_id, current_semester_id=transcript_file.semester_id) + 1
        for cou in course_obj_list:
            DBModel.Major_Course.objects.get_or_create(course_id=cou.pk, major_id=transcript_file.major_id,
                                                       defaults={"semesterRecommended": recommend_semester})
        del recommend_semester
    except Exception as e:
        print(e)
        return False
    course_dict = {cou.courseCode: cou.pk for cou in course_obj_list}

    stu_grade = extraction.getTranscript()
    try:
        for i, row in stu_grade.iterrows():
            # check and create student
            name_arr = studentInfo.loc[i, 'name'].strip().split(' ')
            first_name = name_arr[-1]
            last_name = ' '.join(name_arr[:-1])

            stu, created = DBModel.Profiles.objects.get_or_create(MSSV=i,
                                                                  group_id=transcript_file.group_id,
                                                                  defaults={'gender': studentInfo.loc[i, 'gender'],
                                                                            'firstName': first_name,
                                                                            'lastName': last_name,
                                                                            'birthday': studentInfo.loc[i, 'birth'],
                                                                            'major_id': transcript_file.major_id})
            del name_arr, first_name, last_name
            # check and create grade in transcript
            for course_code, grade in row.items():
                if ~np.isnan(grade):
                    # print("not nan", grade)
                    DBModel.Transcript.objects.update_or_create(course_id=course_dict[course_code],
                                                             student=stu,
                                                             semester_id=transcript_file.semester_id,
                                                             defaults={'grade': round(grade, 2)})

            # update gpa
            calculate_student_gpa(stu, 'update')

    except Exception as e:
        print("ERROR ", e.__dir__(), "\n", e)
        return False

    transcript_file.extracted = True
    transcript_file.save()
    return True

@login_required(login_url='/login/')
def transcript_file_upload(request):
    """
    Thực hiện upload file điểm csv
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    group_id = request.POST['group_id']
    major_id = request.POST['major_id']
    semester_id = request.POST['semester_id']
    transcriptFile = request.FILES['transcriptFile']
    obj, created = DBModel.TranscriptFiles.objects.get_or_create(group_id=group_id,
                                                        major_id= major_id,
                                                        semester_id=semester_id,
                                                        defaults={"extracted": False})
    if ~created:
        try:
            obj.extracted = False
            os.remove(obj.transcript.path)
        except Exception as e:
            print("error learningoutcomeview.py: ", e)

    obj.transcript.save(transcriptFile.name, transcriptFile)
    return obj

@login_required(login_url='/login/')
@require_http_methods(['GET', 'POST'])
def transcript_file_process(request):
    """
    Thực hiện quán trình upload file
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    units = DBModel.Units.objects.all()
    generations = DBModel.Generations.objects.all()
    student_groups = DBModel.StudentGroups.objects.all()
    majors = DBModel.Majors.objects.all()
    semesters = DBModel.Semesters.objects.all()
    transcript_files = DBModel.TranscriptFiles.objects.filter(extracted=False)

    context = {'units': units,
               'generations': generations,
               'student_groups': student_groups,
               'majors': majors,
               'semesters': semesters,
               'transcript_files': transcript_files,
               }

    if request.method == 'POST':
        if request.POST['action'] == 'upload':
            try:
                obj = transcript_file_upload(request)
                context['uploaded_file_url'] = obj.transcript.name
            except Exception as e:
                print(e)
                context['uploaded_file_url'] = "error"
        elif request.POST['action'] == 'extract':
            num_of_Grade = DBModel.Transcript.objects.filter().count()
            extract_success = extract_transcript_file(request)
            num_of_Grade_added = DBModel.Transcript.objects.filter().count() - num_of_Grade

            context['extract_result'] = "success, add {} score(s)".format(num_of_Grade_added) if extract_success else "failed"

    return TemplateResponse(request, 'adminuet/learningoutcomeimport.html', context=context)

@login_required(login_url='/login/')
@api_view(['GET'])
def transcript_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong unit theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            transcripts = Transcript.objects.order_by('-transcriptID').all()
        else:
            transcripts = Transcript.objects.filter(student__major__unit=unitRole).order_by('-transcriptID').all()
        transcriptList = transcripts[offset:offset + limit].select_related('student', 'course', 'semester')
        transcriptCount = transcripts.count()
        transcriptSerializer = TranscriptSerializer(transcriptList, many=True)
        for tl, ts in zip(transcriptList, transcriptSerializer.data):
            ts['studentCode'] = tl.student.MSSV
            ts['student'] = str(tl.student.lastName) + ' ' + str(tl.student.firstName)
            ts['course'] = tl.course.courseName
            ts['semester'] = tl.semester.semesterName
        page = math.ceil(transcriptCount/limit)
        data = {
            'data': transcriptSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Kết quả học tập', '')
        return Response(data)


@login_required(login_url='/login/')
def transcript_delete(request, id):
    """
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        transcript = Transcript.objects.get(pk=id)
        createLog(request, 'DELETE - Kết quả học tập', transcript.student.MSSV + '-' + str(transcript.course))
        transcript.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/learningoutcome/')


@login_required(login_url='/login/')
@api_view(['GET','POST'])
def transcript_form(request, id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """

    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        if request.method == 'GET':
            unitRole = request.user.unit_role
            listProfiles = Profiles.objects.filter(major__unit=unitRole).all()
            cousers = Courses.objects.filter(unit=unitRole).all()

            if id == 0:
                transcriptForm = TranscriptForm()
            else:
                transcripts = Transcript.objects.get(pk=id)
                transcriptForm = TranscriptForm(instance=transcripts)
            return TemplateResponse(request, 'adminuet/learningoutcomeform.html', {'form': transcriptForm, 'listProfiles': listProfiles, 'unitRole': unitRole, 'cousers': cousers})
        else:
            contentMsg = 'Cập nhật thành công.'
            if id == 0:
                transcriptForm = TranscriptForm(request.POST)
                createLog(request, 'INSERT - Kết quả học tập', '')
                contentMsg = 'Thêm mới thành công.'
            else:
                transcripts = Transcript.objects.get(pk=id)
                transcriptForm = TranscriptForm(request.POST, instance=transcripts)
                createLog(request, 'UPDATE - Kết quả học tập', '')
            if transcriptForm.is_valid():
                transcripts = transcriptForm.save()
                calculate_student_gpa(transcripts.student, 'reevaluation')
                messages.success(request, contentMsg)
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/learningoutcome/')

@login_required(login_url='/login/')
def export_page(request):
    """
    Thuộc tính của file csv: stt, roleName, roleDescription
    """

    if checkInUrl(request, 'learningoutcome') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListTranscript")
        unitRole = request.user.unit_role
        if unitRole == 0:
            transcript = Transcript.objects.all()
        else:
            transcript = Transcript.objects.filter(student__major__unit=unitRole).all()
        rows = ([i+1, t.student, t.course, t.semester, t.grade] for t, i in zip(transcript, range(transcript.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['stt', 'student', 'course', 'semeste', 'grade'])
        [writer.writerow([row[0], row[1], row[2], row[3], row[4] ]) for row in rows]
        createLog(request, 'EXPORT - Kết quả học tập', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/learningoutcome/')
