from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd
from mainApp.forms import UnitForm
from mainApp.models import Units, create_from_DF
from mainApp.serializers.unitserializer import UnitSerializer
from mainApp.viewapi.logs import createLog
import csv, io
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from itertools import tee

@login_required(login_url='/login/')
def unitPagination_page(request, num=1, limit=10):
    """
    Hiện thị trang danh sách trường có phân trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/unit.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def unit_getList(request):
    """
    Lấy danh sách các trường (không sử dụng)
    Hàm trả về tất cả các row trong unit
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitList = Units.objects.all()
        unitSerializer = UnitSerializer(unitList, many = True)
        return Response(unitSerializer.data)

@login_required(login_url='/login/')
@api_view(['GET'])
def unit_getListForOffset(request, offset, limit):
    """
    Lấy danh sách các trường tại vị trí offset và limit bản ghi
    Hàm trả về  các row trong unit theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        units = Units.objects.order_by('-unitID').all()
        unitList = units[offset:offset + limit]
        unitCount = units.count()
        unitSerializer = UnitSerializer(unitList, many = True)
        page = math.ceil(unitCount/limit)
        data = {
            'data': unitSerializer.data,
            'numberOfPage': page,
        }
        # Ghi log
        createLog(request, 'VIEW - Trường', '')
        return Response(data)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def unit_form(request, unit_id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try: 
        if request.method == 'GET':
            if unit_id == 0:
                unitForm = UnitForm()
            else:
                unit = Units.objects.get(pk=unit_id)
                unitForm = UnitForm(instance = unit)
            return TemplateResponse(request, 'adminuet/unitform.html', {'form': unitForm})
        else:
            contentLog = 'UPDATE - Trường'
            contentMsg = 'Cập nhật thành công.'
            if unit_id == 0:
                unitForm = UnitForm(request.POST)
                contentLog = 'INSERT - Trường'
                contentMsg = 'Thêm mới thành công.'
            else:
                unit = Units.objects.get(pk=unit_id)
                unitForm = UnitForm(request.POST, instance = unit)
            if unitForm.is_valid():
                unitNameNew = unitForm['unitName'].value()
                if not checkUnitNameExist(unitNameNew.strip()):
                    unitForm.save()
                    # Ghi log
                    createLog(request, contentLog, unitNameNew)
                    messages.success(request, contentMsg)
                else:
                    messages.error(request, 'Vui lòng thay đổi tên đơn vị. Đơn vị này đã tồn tại.')
                    return redirect('/adminuet/unit-form/'+str(unit_id))
            return redirect('/adminuet/unit/')
    except Exception:
        messages.error(request, "Thao tác thất bại.")
        return redirect('/adminuet/unit/')

def checkUnitNameExist(unitname):
    """
    Kiểm tra trường có tồn tại trong DB
    """
    if Units.objects.filter(unitName=unitname).exists():
        return True

@login_required(login_url='/login/')
def unit_delete(request, unit_id):
    """
    Thực hiện xóa trường
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unit = Units.objects.get(pk=unit_id)
        name = unit.unitName
        unit.delete()
        # Ghi log
        createLog(request, 'DELETE - Trường', name)
        messages.success(request, "Xóa thành công.")
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/unit/')

@login_required(login_url='/login/')
def import_page(request):
    """
    Đọc file csv để nhập vào DB
    Hàm nhập từ file csv các trường stt, unitName, unitDescription vào model Units
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/unitimport.html'
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
        create_from_DF(df=df, model=Units, searching_cols=['unitName'])
        # Ghi log
        message =  str(len(df)) + ' bản ghi'
        createLog(request, 'IMPORT - Trường', message)
    except (Exception) as error:
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/unit/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Xuất danh sách các trường ra file csv
    Hàm xuất từ danh sách trường ra file csv
    """
    if checkInUrl(request, 'unit') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListUnit")
        list_unit = Units.objects.all()
        rows = ([i+1, unit.unitName, unit.unitDescription] for unit, i in zip(list_unit, range(list_unit.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        rows, rowCopy = tee(rows)
        # Ghi log
        createLog(request, 'EXPORT - Trường', str(len(list(rowCopy))) + ' bản ghi')
        writer.writerow(['stt', 'unitName', 'unitDescription'])
        [writer.writerow([row[0], row[1], row[2]]) for row in rows]
        createLog(request, 'EXPORT - Trường', '')
        return response
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/unit/')