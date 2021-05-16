from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from mainApp.models import Semesters, Years
from mainApp.forms import SemesterForm
from mainApp.serializers.semesterserializer import SemesterSerializer
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog

import pandas as pd
import csv
from django.http import HttpResponse
from mainApp.models import create_from_DF


@login_required(login_url='/login/')
def semesterPagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách các kỳ học có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/semester.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def semester_getList(request):
    """
    Lấy danh sách các kỳ học (không sử dụng)
    Hàm trả về tất cả các row trong semesters 
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        semesterList = Semesters.objects.all()
        semesterSerializer = SemesterSerializer(semesterList, many = True)
        return Response(semesterSerializer.data)


@login_required(login_url='/login/')
@api_view(['GET'])
def semester_getListForOffset(request, offset, limit):
    """
    Lấy danh sách các kỳ học từ vị trị offset và limit bản ghi
    Hàm trả về  các row trong semester theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        semesters = Semesters.objects.order_by('semesterID').all()
        semesterList = semesters[offset:offset + limit].select_related('year')
        semesterCount = semesters.count()
        semesterSerializer = SemesterSerializer(semesterList, many = True)
        for sS, sL in zip(semesterSerializer.data, semesterList):
            sS['year'] = sL.year.yearName
            if sS['beginDay'] is None:
                sS['beginDay'] = "Chưa có dữ liệu"
            if sS['endDay'] is None:
                sS['endDay'] = "Chưa có dữ liệu"
        page = math.ceil(semesterCount/limit)
        data = {
            'data': semesterSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Học kỳ', '')
        return Response(data)


@login_required(login_url='/login/')
@api_view(['GET','POST'])
def semester_form(request, id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        if request.method == 'GET':
            if id == 0:
                semesterForm = SemesterForm()
            else:
                semester = Semesters.objects.get(pk=id)
                semesterForm = SemesterForm(instance = semester)
            return TemplateResponse(request, 'adminuet/semesterform.html', {'form': semesterForm})
        else:
            contentLog = 'UPDATE - Học kỳ'
            contentMsg = 'Cập nhật thành công.'
            if id == 0:
                semesterForm = SemesterForm(request.POST)
                contentLog = 'INSERT - Học kỳ'
                contentMsg = 'Thêm mới thành công.'
            else:
                semester = Semesters.objects.get(pk=id)
                semesterForm = SemesterForm(request.POST, instance = semester)
            if semesterForm.is_valid():
                semesterNameNew = semesterForm['semesterName'].value()
                semesterYearNew = semesterForm['year'].value()
                semesterBeginDayNew = semesterForm['beginDay'].value()
                semesterEndDayNew = semesterForm['endDay'].value()
                if semesterBeginDayNew == "" and semesterEndDayNew == "":
                    semesterBeginDayNew = "2000-06-20"
                    semesterEndDayNew = "2000-06-21"
                if not checkSemesterNameAndYearExist(semesterNameNew, semesterYearNew, semesterBeginDayNew, semesterEndDayNew): 
                    if checkCompareBeginDayAndEndDay(semesterBeginDayNew, semesterEndDayNew):
                        semesterForm.save()
                        createLog(request, contentLog , str(semesterNameNew))
                        messages.success(request, contentMsg)
                    else:
                        messages.error(request, 'Vui lòng thay đổi thời gian bắt đầu và thời gian kết thúc.')
                        return redirect('/adminuet/semester-form/'+str(id))
                else: 
                    messages.error(request, 'Vui lòng thay đổi kỳ học. Kỳ học này đã tồn tại.')
                    return redirect('/adminuet/semester-form/'+str(id))
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/semester/')

def checkSemesterNameAndYearExist(semestername, yearid, begin, end):
    """
    Kiểm tra kỳ học có tồn tại không
    """
    if Semesters.objects.filter(semesterName=semestername, year=yearid, beginDay=begin, endDay=end).exists():
        return True

def checkCompareBeginDayAndEndDay(beginDay, endDay):
    """
    Kiểm tra ngày kết thúc có lớp hơn ngày bắt đầu không
    """
    return beginDay < endDay

@login_required(login_url='/login/')
def semester_delete(request, id):
    """
    Thực hiện xóa kỳ học
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        semester = Semesters.objects.get(pk=id)
        createLog(request, 'DELETE - Học kỳ', semester.semesterName)
        semester.delete()
        messages.success(request, "Xóa thành công.")
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/semester/')


@login_required(login_url='/login/')
def import_page(request):
    """
    Hàm nhập từ file csv các trường stt, semester, year, beginDay, endDay vào model Semesters
    """

    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/semesterimport.html'
    if request.method == 'GET':
        return TemplateResponse(request, template)
    try:
        csv_file = request.FILES['document']
    except (Exception) as error:
        messages.error(request,'Lỗi: Chưa chọn tệp dữ liệu.')
        return TemplateResponse(request, template)
    if not csv_file.name.endswith('.csv'):
        messages.error(request,'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
        return TemplateResponse(request, template)
    try:
        df = pd.read_csv(csv_file).set_index("stt")
        years = Years.objects.all()
        dict_year = {}
        for year in years:
            dict_year[year.yearName.lower()] = year.yearID
        for i, row in df.iterrows():
            if row['year_id'].lower() in dict_year:
                row['year_id'] = dict_year[row['year_id'].lower()]
            else:
                messages.error(request,'Lỗi: Trong hệ thống không tồn tại ' + row['year'] + '.')
                return TemplateResponse(request, template)
            if checkCompareBeginDayAndEndDay(row['beginDay'], row['endDay']) is False:
                messages.error(request,'Lỗi: Begin day lớn hơn end day ở hàng ' + str(row['stt']) + '.')
                return TemplateResponse(request, template)
            print(row['year_id'])
        create_from_DF(df=df, model=Semesters, searching_cols=['semesterName','year_id','beginDay', 'endDay'])
    except (Exception) as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.', error)
        return TemplateResponse(request, template)
    return redirect('/adminuet/semester/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Hàm xuất từ danh sách học ky ra file csv
    """
    if checkInUrl(request, 'semester') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListSemester")
        list_semester = Semesters.objects.all()
        rows = ([i+1, semester.semesterName, semester.year ] for semester, i in zip(list_semester, range(list_semester.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        writer.writerow(['stt', 'semesterName', 'year'])
        [writer.writerow([row[0], row[1], row[2]]) for row in rows]
        createLog(request, 'EXPORT - Học kỳ', '')
        return response
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/semester/')