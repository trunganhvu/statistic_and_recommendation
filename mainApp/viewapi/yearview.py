from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from mainApp.models import Years, Semesters
from mainApp.forms import YearForm
from mainApp.serializers.yearserializer import YearSerializer
import math
import pandas as pd
import csv, io
from django.http import HttpResponse
from mainApp.models import update_from_DF, create_from_DF
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog

@login_required(login_url='/login/')
def yearPagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách các năm học có trang, giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/year.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def year_getList(request):
    """
    Lấy danh sách tất cả năm học
    Hàm trả về tất cả các row trong year 
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        yearList = Years.objects.all()
        yearSerializer = YearSerializer(yearList, many = True)
        return Response(yearSerializer.data)


@login_required(login_url='/login/')
@api_view(['GET'])
def year_getListForOffset(request, offset, limit):
    """
    Lấy danh sách các năm học từ vị trí và limit bản ghi
    Hàm trả về  các row trong year theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        years = Years.objects.order_by('-yearID').all()
        yearList = years[offset:offset + limit]
        yearCount = years.count()
        yearSerializer = YearSerializer(yearList, many = True)
        page = math.ceil(yearCount/limit)
        for year in yearSerializer.data:
            if str(year['active']).lower() == 'true': 
                year['active'] = 'Kích hoạt'
            else: 
                year['active'] = 'Không kích hoạt'
        data = {
            'data': yearSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Năm học', '')
        return Response(data)

def auto_generate_semesters(year):
    semesters = Semesters.objects.filter(year_id=year.pk)
    if len(semesters) <= 0:
        sem1 = Semesters(semesterName=year.yearName + " kỳ 1", year_id=year.pk)
        sem2 = Semesters(semesterName=year.yearName + " kỳ 2", year_id=year.pk)

        last_sem = Semesters.objects.filter(endDay__year=year.openingDay.year).order_by('-endDay')
        if len(last_sem) >= 1:
            last_sem_end = last_sem[0].endDay
        else:
            last_sem_end = None

        next_sem = Semesters.objects.filter(beginDay__year__gt=year.openingDay.year).order_by('beginDay')
        if len(next_sem) >= 1:
            next_sem_begin = next_sem[0].beginDay
        else:
            next_sem_begin = None

        if year.openingDay is not None :
            ny = year.openingDay.year + 1
            sem1.beginDay = year.openingDay
            sem1.endDay = datetime.strptime(str(ny) + '-01-31', "%Y-%m-%d").date()
            sem2.beginDay = datetime.strptime(str(ny) + '-02-01', "%Y-%m-%d").date()
            sem2.endDay = datetime.strptime(str(ny) + '-06-01', "%Y-%m-%d").date()
            if (last_sem_end is None or sem1.beginDay > last_sem_end) and (next_sem_begin is None or sem2.endDay < next_sem_begin):
                last_sem = Semesters.objects.last()
                last_pk = 0 if last_sem is None else last_sem.pk

                sem1.pk = last_pk + 1
                sem2.pk = last_pk + 2

                sem1.save()
                sem2.save()
                return True
    return False

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def year_form(request, id=0, generate_semesters=True):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """

    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        if request.method == 'GET':
            if id == 0:
                yearForm = YearForm()
            else:
                year = Years.objects.get(pk=id)
                yearForm = YearForm(instance = year)
            return TemplateResponse(request, 'adminuet/yearform.html', {'form': yearForm})
        else:
            contentLog = 'UPDATE - Năm học'
            contentMsg = 'Cập nhật thành công'
            if id == 0:
                yearForm = YearForm(request.POST)
                contentLog = 'INSERT - Năm học'
                contentMsg = "Thêm mới thành công."
            else:
                year = Years.objects.get(pk=id)
                yearForm = YearForm(request.POST, instance=year)
            if yearForm.is_valid():
                yearNameNew = yearForm['yearName'].value()
                status = yearForm['active'].value()

                if not checkYearNameExist(yearNameNew.strip(), status):
                    try:
                        year = yearForm.save()
                        if generate_semesters:
                            auto_generate_semesters(year=year)
                        createLog(request, contentLog, yearNameNew)
                        messages.success(request, contentMsg)
                    except Exception as e:
                        messages.error(request, 'Vui lòng thay đổi ngày khai giảng. Mỗi năm chỉ tồn tại một ngày khai giảng.')
                        return redirect('/adminuet/year-form/' + str(id))

                else:
                    messages.error(request, 'Vui lòng thay đổi năm học. Năm học này đã tồn tại.')
                    return redirect('/adminuet/year-form/'+str(id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/year/')

def checkYearNameExist(yearname, status):
    """
    Kiểm tra năm học đã tồn tại chưa
    """
    if Years.objects.filter(yearName=yearname).filter(active=status).exists():
        return True

@login_required(login_url='/login/')
def year_delete(request, id):
    """
    Thực hiện xóa năm học
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        year = Years.objects.get(pk=id)
        createLog(request, 'DELETE - Năm học', year.yearName)
        year.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/year/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Xuất danh sách năm học ra file csv
    Hàm xuất từ danh sách năm học ra file csv
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListYear")
        list_year = Years.objects.all()
        rows = ([i+1, year.yearName, year.active ] for year, i in zip(list_year, range(list_year.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        writer.writerow(['stt', 'yearName', 'active'])
        for row in rows:
            if str(row[2]).lower() == 'true': row[2] = 'Kích hoạt'
            elif str(row[2]).lower() == 'false': row[2] = 'Không kích hoạt'
            writer.writerow([row[0], row[1], row[2]])
        createLog(request, 'EXPORT - Năm học', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/year/')

@login_required(login_url='/login/')
def import_page(request):
    """
    Thực hiện đọc file csv để nhập vào DB
    Hàm xuất từ danh sách năm học ra file csv
    Các trường stt, yearName, active
    """
    if checkInUrl(request, 'year') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/yearimport.html'
    if request.method == 'GET':
        return TemplateResponse(request, template)
    try:
        csv_file = request.FILES['document']
    except (Exception) as error:
        print(error)
        messages.error(request, 'Lỗi: Chưa chọn tệp dữ liệu.')
        return TemplateResponse(request, template)
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
        return TemplateResponse(request, template)
    try:
        df = pd.read_csv(csv_file).set_index("stt")
        for i, row in df.iterrows():
            df.loc[i, 'openingDay'] = datetime.strptime(row['openingDay'], "%Y-%m-%d").date()

            if str(row['active']).lower() == "kích hoạt":
                df.loc[i, 'active'] = True
            elif str(row['active']).lower() == "không kích hoạt":
                df.loc[i, 'active'] = False
            else:
                df.drop(i)

        year_list = create_from_DF(df=df, model=Years, searching_cols=['yearName'])
        for year in year_list:
            auto_generate_semesters(year)
    except Exception as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/year/')


