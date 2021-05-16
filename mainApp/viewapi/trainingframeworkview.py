from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd
from mainApp.forms import TrainingframeworkForm
from mainApp.models import Major_Course, update_from_DF, create_from_DF, Echo, Courses, Majors, Units
from mainApp.serializers.trainingframewordserializer import TrainingframeworkSerializer
import csv, io
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog

@login_required(login_url='/login/')
def trainingframeworkPagination_page(request, num=1, limit=10):
    """
    Hiện thị trang danh sách chương trình đào tạo có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/trainingframework.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def trainingframework_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong unit theo offset
    Trả về số lượng page mà chia theo limit
    """

    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            trainingframeworks = Major_Course.objects.order_by('-ID').all()
        else:
            trainingframeworks = Major_Course.objects.filter(major__unit=unitRole).order_by('-ID').all()
        trainingframeworkList = trainingframeworks[offset:offset + limit].select_related('course', 'major')
        trainingframeworkCount = trainingframeworks.count()
        trainingframeworkSerializer = TrainingframeworkSerializer(trainingframeworkList, many = True)
        for t, ts in zip(trainingframeworkList, trainingframeworkSerializer.data):
            ts['course'] = t.course.courseName
            ts['major'] = t.major.majorName
        page = math.ceil(trainingframeworkCount/limit)
        data = {
            'data': trainingframeworkSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Khung đào tạo', '')
        return Response(data)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def trainingframework_form(request, id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """

    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        cousers = Courses.objects.filter(unit=unitRole).all()
        majors = Majors.objects.filter(unit=unitRole).all()
        if request.method == 'GET':
            if id == 0:
                trainingframeworkForm = TrainingframeworkForm()
            else:
                major_Course = Major_Course.objects.get(pk=id)
                trainingframeworkForm = TrainingframeworkForm(instance=major_Course)
            return TemplateResponse(request, 'adminuet/trainingframeworkform.html', {'form': trainingframeworkForm, 'cousers': cousers, 'unitRole': unitRole, 'majors': majors})
        else:
            contentLog = 'UPDATE - Khung đào tạo'
            contentMsg = 'Cập nhật thành công.'
            if id == 0:
                trainingframeworkForm = TrainingframeworkForm(request.POST)
                contentLog = 'INSERT - Khung đào tạo'
                contentMsg = 'Thêm mới thành công.'
            else:
                major_Course = Major_Course.objects.get(pk=id)
                trainingframeworkForm = TrainingframeworkForm(request.POST, instance=major_Course)
            if trainingframeworkForm.is_valid():
                trainingframeworkForm.save()
                createLog(request, contentLog, '')
                messages.success(request, contentMsg)
                # unitNameNew = unitForm['unitName'].value()
                # if not checkUnitNameExist(unitNameNew.strip()):
                #     unitForm.save()
                # else:
                #     messages.error(request, 'Vui lòng thay đổi tên đơn vị. Đơn vị này đã tồn tại.')
                #     return redirect('/adminuet/trainingframework-form/'+str(id))
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/trainingframework/')


@login_required(login_url='/login/')
def trainingframework_delete(request, id):
    """
    Xóa chương trình đào tạo
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        majorcourse = Major_Course.objects.get(pk=id)
        createLog(request, 'DELETE - Khung đào tạo', str(majorcourse.major.majorName) + ' - ' +str(majorcourse.course.courseName))
        majorcourse.delete()
        messages.success(request, "Xóa thành công.")
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/trainingframework/')

@login_required(login_url='/login/')
def import_page(request):
    """
    Đọc file csv để nhập vào DB
    Hàm nhập từ file csv các trường Course, Semester_Recommend
    """
    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/trainingframeworkimport.html'
    units = Units.objects.all()
    context = {
        'units': units,
    }
    if request.method == 'GET':
        return TemplateResponse(request, template, context=context)
    if request.method == 'POST':
        unitInput = request.POST['unit']
        majorInput = request.POST['major']
        checkUnit = Units.objects.filter(unitID=unitInput)
        checkMajor = Majors.objects.filter(majorID=majorInput)
        # Kiểm tra unitID và majorID client gửi lên có tồn tại không
        if checkUnit.exists() and checkMajor.exists():
            try:
                csv_file = request.FILES['document']
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Chưa chọn tệp dữ liệu.')
                return TemplateResponse(request, template, context=context)
            if not csv_file.name.endswith('.csv'):
                messages.error(request,'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
                return TemplateResponse(request, template, context=context)
            try:
                df = pd.read_csv(csv_file)
                courses = Courses.objects.all()
                dict_course = {}
                for course in courses:
                    dict_course[course.courseName.lower()] = course.courseID
                for i, row in df.iterrows():
                    # Kiểm tra course_id=coursename có tồn tại trong dict_course(có trong db)
                    if row['Course'].lower() in dict_course:
                        df.at[i, 'Course'] = dict_course[row['Course'].lower()]
                    else:
                        messages.error(request,'Lỗi: Không có môn ' + row['course_id'] + '.')
                        return TemplateResponse(request, template)
                    courseID = dict_course[row['Course'].lower()]
                    semesterRecommend = row['Semester_Recommend']
                    try:
                        toDatabase = Major_Course(course_id=courseID, major_id=majorInput, semesterRecommended=semesterRecommend)
                        toDatabase.save()
                    except (Exception) as error:
                        print(error)
                # dict_course = {}
                # dict_major = {}
                # for course in courses:
                #     dict_course[course.courseName.lower()] = course.courseID
                # for major in majors:
                #     dict_major[major.majorName.lower()] = major.majorID
                # for i, row in df.iterrows():
                #     # Kiểm tra course_id=coursename có tồn tại trong dict_course(có trong db)
                #     if row['course_id'].lower() in dict_course:
                #         df.at[i, 'course_id'] = dict_course[row['course_id'].lower()]
                #     else:
                #         messages.error(request,'Lỗi: Không có môn ' + row['course_id'] + '.')
                #         return TemplateResponse(request, template)
                #     # Kiểm tra major_id=majorName có tồn tại trong dict_major(có trong db)
                #     if row['major_id'].lower() in dict_major:
                #         df.at[i, 'major_id'] = dict_major[row['major_id'].lower()]
                #     else:
                #         messages.error(request,'Lỗi: Không có môn ' + row['major_id'] + '.')
                #         return TemplateResponse(request, template)
                # create_from_DF(df=df, model=Major_Course, searching_cols=['semesterRecommended', 'course_id', 'major_id'])
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
                return TemplateResponse(request, template, context=context)
            return redirect('/adminuet/trainingframework/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Xuất danh sách các chương trình đào tạo ra file csv
    Hàm xuất từ danh sách trường ra file csv
    """
    if checkInUrl(request, 'trainingframework') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try: 
        unitRole = request.user.unit_role
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListTrainingframework")
        if unitRole == 0:
            list_majorcourse = Major_Course.objects.all()
        else:
            list_majorcourse = Major_Course.objects.filter(major__unit=unitRole).all()
        rows = ([i+1, majorcourse.course, majorcourse.major, majorcourse.semesterRecommended ] for majorcourse, i in zip(list_majorcourse, range(list_majorcourse.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        writer.writerow(['stt', 'course', 'major', 'semesterRecommended'])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], row[3]])
        createLog(request, 'EXPORT - Khung đào tạo', '')
        return response
    except (Exception) as error:
        print(error)
    return redirect('/adminuet/trainingframework/')