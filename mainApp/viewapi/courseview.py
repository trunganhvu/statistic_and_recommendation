from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from mainApp.forms import CoursesForm
from mainApp.models import Courses, Units
from mainApp.serializers.cousersserializer import CoursesSerializer
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog

from django.http import HttpResponse
import pandas as pd
import csv


@login_required(login_url='/login/')
def coursePagination_page(request, num=1, limit=10):
    """
    Hiển thị trang môn học với trang và số lượng bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/course.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def course_getList(request):
    """
    Lấy danh sách các môn học - Không sử dụng
    Hàm trả về tất cả các row trong course
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        courseList = Courses.objects.all()
        courseSerializer = CoursesSerializer(courseList, many = True)
        return Response(courseSerializer.data)


@login_required(login_url='/login/')
@api_view(['GET'])
def course_getListForOffset(request, offset, limit):
    """
    Lấy danh sách các môn học có số lượng và từ vị trí offset
    Phụ thuộc vào vai trò
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        # Rule admin
        if unitRole == 0:
            courses = Courses.objects.order_by('-courseID').all()
        else: # Quản trị cấp trường
            courses = Courses.objects.order_by('-courseID').filter(unit=unitRole).all()
        courseList = courses[offset:offset + limit].select_related('unit')
        courseCount = courses.count()
        courseSerializer = CoursesSerializer(courseList, many = True)
        page = math.ceil(courseCount/limit)
        for cS, cL in zip(courseSerializer.data, courseList):
            cS['unit'] = cL.unit.unitName
        data = {
            'data': courseSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Môn học', '')
        return Response(data)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def course_form(request, course_id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        if request.method == 'GET':
            # Rule admin
            if course_id == 0:
                courseForm = CoursesForm()
            else: # Rule quản trị cấp trường
                course = Courses.objects.get(pk=course_id)
                courseForm = CoursesForm(instance=course)
            return TemplateResponse(request, 'adminuet/courseform.html', {'form': courseForm, 'unitRole': unitRole})
        else: # POST
            # Rule admin
            if course_id == 0:
                courseForm = CoursesForm(request.POST)
            else: #Rule quản trị cấp trường
                course = Courses.objects.get(pk=course_id)
                courseForm = CoursesForm(request.POST, instance = course)

            courseNameNew = courseForm['courseName'].value()
            courseCodeNew = courseForm['courseCode'].value()
            creditNew = courseForm['credit'].value()
            unitIDNew = unitRole 

            if courseForm['unit'].value() is not None:
                unitIDNew = courseForm['unit'].value()
            
            if not checkCourseNameAndUnitExist(courseNameNew.strip(), unitIDNew) and courseNameNew.strip():
                if course_id == 0:
                    courseInsert = Courses(unit_id=unitIDNew, courseCode=courseCodeNew, courseName=courseNameNew, credit=creditNew)
                    courseInsert.save()
                    createLog(request, 'INSERT - Môn học', courseNameNew)
                    messages.success(request, "Thêm mới thành công.")
                else:
                    courseUpdate = Courses.objects.get(pk=course_id)
                    courseUpdate.unit_id = unitIDNew
                    courseUpdate.courseCode = courseCodeNew
                    courseUpdate.courseName = courseNameNew
                    courseUpdate.credit = creditNew
                    courseUpdate.save()
                    createLog(request, 'UPDATE - Môn học', courseNameNew)
                    messages.success(request, "Cập nhật thành công.")
            else:
                messages.error(request, 'Vui lòng thay đổi tên môn học. Môn học này đã tồn tại.')
                return redirect('/adminuet/course-form/'+str(course_id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/course/')


def checkCourseNameAndUnitExist(coursename, unitid):
    """
    Kiểm tra sự tồn tại của môn học bằng tên
    """
    if Courses.objects.filter(courseName=coursename, unit=unitid).exists():
        return True


@login_required(login_url='/login/')
def course_delete(request, course_id):
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        course = Courses.objects.get(pk=course_id)
        createLog(request, 'DELETE - Môn học', str(course.courseCode))
        course.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/course/')



@login_required(login_url='/login/')
def export_page(request):
    """
    Thực hiện xuất file các môn học
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    nameFileExport = 'attachment; filename="{}.csv"'.format("ListCourse")
    unitRole = request.user.unit_role
    if unitRole == 0:
        list_course = Courses.objects.all().select_related('unit')
    else:
        list_course = Courses.objects.filter(unit=unitRole).all().select_related('unit')
    rows = ([i+1, course.courseCode, course.courseName, course.unit.unitName, course.credit ] for course, i in zip(list_course, range(list_course.count())))
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = nameFileExport
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['stt', 'courseCode', 'courseName', 'unit', 'credit'])

    for r in rows:
        writer.writerow([r[0], r[1], r[2], r[3], r[4]])
    createLog(request, 'EXPORT - Môn học', '')
    return response

@login_required(login_url='/login/')
def import_page(request):
    """
    Thực hiện đọc file để nhập liệu
    Các thuộc tính của file csv: stt, courseCode, courseName, credit, unit_id
    """
    if checkInUrl(request, 'course') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/courseimport.html'
    units = Units.objects.all()
    context = {
        'units': units,
    }
    if request.method == 'GET':
        return TemplateResponse(request, template, context=context)
    if request.method == 'POST':
        unitInput = request.POST['unit']
        checkUnit = Units.objects.filter(unitID=unitInput)
        # Kiểm tra unitID client gửi lên có tồn tại không
        if checkUnit.exists():
            try:
                csv_file = request.FILES['document']
            except (Exception) as error:
                messages.error(request,'Lỗi: Chưa chọn tệp dữ liệu.')
                return TemplateResponse(request, template, context=context)
            if not csv_file.name.endswith('.csv'):
                messages.error(request,'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
                return TemplateResponse(request, template, context=context)
            try:
                df = pd.read_csv(csv_file)
                unitId = -1
                for u in checkUnit:
                    unitId = u.unitID
                # đọc từng dòng có trong file csv
                for i, row in df.iterrows():
                    courseCode = row['Course_Code']
                    courseName = row['Course_Name']
                    credit = row['Credit']
                    try:
                        toDatabase = Courses(unit_id=unitId, courseCode=courseCode, courseName=courseName, credit=credit)
                        toDatabase.save()
                    except (Exception) as error:
                        print(error)   
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
                return TemplateResponse(request, template, context=context)
            return redirect('/adminuet/course/')
        else:
            messages.error(request,'Lỗi: Đã xảy ra lỗi vui lòng thử lại.')
            context['lastUnitInput'] = unitInput
            return TemplateResponse(request, template, context=context)

