from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import redirect
from django.contrib import messages
from mainApp.models import Majors, Units
from mainApp.forms import MajorsForm
from mainApp.serializers.majorserializer import MajorSerializer
from mainApp.viewapi.logs import createLog
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse

import pandas as pd
import csv
from django.http import HttpResponseRedirect

from django.http import HttpResponse
from itertools import tee


@login_required(login_url='/login/')
def majorPagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách ngành có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/major.html', {'page': num, 'limit': limit})


@login_required(login_url='/login/')
@api_view(['GET'])
def major_getList(request):
    """
    Lấy toàn bộ danh sách các ngành (không sử dụng)
    Hàm trả về tất cả các row trong major
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        majorList = Majors.objects.all()
        majorSerializer =MajorSerializer(majorList, many = True)
        return Response(majorSerializer.data)


@login_required(login_url='/login/')
@api_view(['GET'])
def major_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong major theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        if unitRole == 0:
            majors = Majors.objects.order_by('-majorID').all()
        else:
            majors = Majors.objects.order_by('-majorID').filter(unit=unitRole).all()
        majorList = majors[offset:offset + limit].select_related('unit')
        majorCount = majors.count()
        majorSerializer = MajorSerializer(majorList, many = True)
        page = math.ceil(majorCount/limit)
        for mS, mL in zip(majorSerializer.data, majorList):
            mS['unit'] = mL.unit.unitName
        data = {
            'data': majorSerializer.data,
            'numberOfPage': page,
        }
        # Ghi log
        createLog(request, 'VIEW - Ngành', '')
        return Response(data)


@login_required(login_url='/login/')
@api_view(['GET','POST'])
def major_form(request, major_id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """

    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        if request.method == 'GET':
            if major_id == 0:
                majorForm = MajorsForm()
            else:
                major = Majors.objects.get(pk=major_id)
                majorForm = MajorsForm(instance = major)
            return TemplateResponse(request, 'adminuet/majorform.html', {'form': majorForm, 'unitRole': unitRole})
        else:
            if major_id == 0:
                majorForm = MajorsForm(request.POST)
            else:
                major = Majors.objects.get(pk=major_id)
                majorForm = MajorsForm(request.POST, instance = major)

            majorNameNew = majorForm['majorName'].value()
            majorDescriptionNew = majorForm['majorDescription'].value()
            unitIDNew = unitRole
            if majorForm['unit'].value() is not None:
                unitIDNew = majorForm['unit'].value()
            if not checkSemesterNameAndYearExist(majorNameNew, majorDescriptionNew, unitIDNew):
                if major_id == 0:
                    majorInsert = Majors(unit_id=unitIDNew, majorName=majorNameNew, majorDescription=majorDescriptionNew)
                    majorInsert.save()
                    createLog(request, 'INSERT - Ngành', majorNameNew)
                    messages.success(request, "Thêm mới thành công.")
                else:
                    majorUpdate = Majors.objects.get(pk=major_id)
                    majorUpdate.unit_id = unitIDNew
                    majorUpdate.majorName = majorNameNew
                    majorUpdate.majorDescription = majorDescriptionNew
                    majorUpdate.save()
                    createLog(request, 'UPDATE - Ngành', majorNameNew)
                    messages.success(request, "Cập nhật thành công.")

                # Ghi log
            else: 
                messages.error(request, 'Vui lòng thay đổi thông tin. Ngành đào tạo này đã tồn tại.')
                return redirect('/adminuet/major-form/'+str(major_id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/major/')


def checkSemesterNameAndYearExist(majorname, majordescr, unit):
    """
    Kiểm tra tồn tại ngành trùng không
    """
    if Majors.objects.filter(majorName=majorname, majorDescription=majordescr, unit=unit).exists():
        return True


@login_required(login_url='/login/')
def major_delete(request, major_id):
    """
    Xóa ngành
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        major = Majors.objects.get(pk=major_id)
        # Ghi log
        createLog(request, 'DELETE - Ngành', major.majorName)
        major.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/major/')


@login_required(login_url='/login/')
def import_page(request):
    """
    Thực hiện đọc file csv để thêm vào DB
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/majorimport.html'
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
                context['lastUnitInput'] = unitInput
                return TemplateResponse(request, template, context=context)
            if not csv_file.name.endswith('.csv'):
                context['lastUnitInput'] = unitInput
                messages.error(request,'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
                return TemplateResponse(request, template, context=context)
            try:
                df = pd.read_csv(csv_file)
                unitId = -1
                for u in checkUnit:
                    unitId = u.unitID
                count = 0
                # đọc từng dòng có trong file csv
                for i, row in df.iterrows():
                    majorName = row['Major']
                    majorDescription = row['Major_Description']
                    try:
                        toDatabase = Majors(unit_id=unitId,majorName=majorName, majorDescription=majorDescription)
                        toDatabase.save()
                        count +=1
                    except (Exception) as error:
                        print(error)
                # Ghi log
                createLog(request, 'IMPORT - Ngành', str(count) + ' bản ghi')
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
                context['lastUnitInput'] = unitInput
                return TemplateResponse(request, template, context=context)
            return redirect('/adminuet/major/')
        else:
            messages.error(request,'Lỗi: Đã xảy ra lỗi vui lòng thử lại.')
            context['lastUnitInput'] = unitInput
            return TemplateResponse(request, template, context=context)


@login_required(login_url='/login/')
def export_page(request):
    """
    Thực hiện xuất danh sách các ngành ra fle csv
    """
    if checkInUrl(request, 'major') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListMajor")
        if unitRole == 0:
            list_major = Majors.objects.all()
        else:
            list_major = Majors.objects.filter(unit=unitRole)
        rows = ([i+1, major.majorName, major.unit, major.majorDescription] for major, i in zip(list_major, range(list_major.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        rows, rowCopy = tee(rows)
        # Ghi log
        createLog(request, 'EXPORT - Ngành', str(len(list(rowCopy))) + ' bản ghi')
        writer.writerow(['stt', 'majorName', 'unit', 'majorDescription'])
        [writer.writerow([row[0], row[1], row[2], row[3]]) for row in rows]
        createLog(request, 'EXPORT - Ngành', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/major/')