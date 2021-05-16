from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd
import csv, io
import math
from mainApp.forms import GenerationForm
from mainApp.models import Generations, update_from_DF, create_from_DF, Echo, Units, Years
from mainApp.serializers.generationserializer import GenerationSerializer
from mainApp.serializers.unitserializer import UnitSerializer 
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
from django.http import HttpResponse

"""
Hiển thị trang danh sách các khóa có trang và giới hạn bản ghi (chưa có dữ liệu)
"""
@login_required(login_url='/login/')
def generationPagination_page(request, num=1, limit=10):
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/generation.html', {'page': num, 'limit': limit})


@login_required(login_url='/login/')
@api_view(['GET'])
def generation_getListForOffset(request, offset, limit):
    """Lấy danh sách các khóa từ vị trí offset limit số bản ghi
    Hàm trả về  các row trong unit theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        # Rule admin
        if unitRole == 0:
            generations = Generations.objects.order_by('-generationID').all()
        else: # Rule quản trị cấp trường
            generations = Generations.objects.order_by('-generationID').filter(unit=unitRole).all()
        generationList = generations[offset:offset + limit].select_related('beginningYear','unit')
        generationCount = generations.count()
        generationSerializer = GenerationSerializer(generationList, many = True)
        for p, row in zip(generationList, generationSerializer.data):
            row['beginningYear'] = p.beginningYear.yearName
            row['unit'] = p.unit.unitName
        page = math.ceil(generationCount/limit)
        data = {
            'data': generationSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Khóa', '')
        return Response(data)


@login_required(login_url='/login/')
@api_view(['GET','POST'])
def generation_form(request, generation_id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        if request.method == 'GET':
            if generation_id == 0:
                form = GenerationForm()
            else:
                generation = Generations.objects.get(pk=generation_id)
                form = GenerationForm(instance = generation)
            return TemplateResponse(request, 'adminuet/generationform.html', {'form': form, 'unitRole': unitRole})
        else:
            if generation_id == 0:
                form = GenerationForm(request.POST)
            else:
                generation = Generations.objects.get(pk=generation_id)
                form = GenerationForm(request.POST, instance = generation)

            generationNameNew = form['generationName'].value()
            generationBeginYearNew = form['beginningYear'].value()
            unit = unitRole #form['unit'].value()
            if form['unit'].value() is not None:
                unit = form['unit'].value()
            
            if not checkExist(generationNameNew.strip(), generationBeginYearNew, unit):
                if generation_id == 0:
                    generationInsert = Generations(generationName=generationNameNew, beginningYear_id=generationBeginYearNew, unit_id=unit)
                    generationInsert.save()
                    createLog(request, 'INSERT - Khóa', unit)
                    messages.success(request, "Thêm mới thành công.")
                else:
                    generationUpdate = Generations.objects.get(pk=generation_id)
                    generationUpdate.unit_id = unit
                    generationUpdate.generationName = generationNameNew
                    generationUpdate.beginningYear_id = generationBeginYearNew
                    generationUpdate.save()
                    createLog(request, 'UPDATE - Khóa', unit)
                    messages.success(request, "Cập nhật thành công.")

            else:
                messages.error(request, 'Vui lòng thay đổi khóa. Khóa này đã tồn tại.')
                return redirect('/adminuet/generation-form/'+str(generation_id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/generation/')


def checkExist(name, year, unit):
    """
    Kiểm tra sự tồn tại của khóa theo trường và năm bắt đầu
    """
    if Generations.objects.filter(generationName=name, beginningYear=year, unit=unit).exists():
        return True


@login_required(login_url='/login/')
def generation_delete(request, generation_id):
    """
    Thực hiên xóa 1 khóa
    """
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        generation = Generations.objects.get(pk=generation_id)
        createLog(request, 'DELETE - Khóa', generation.generationName)
        generation.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/generation/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Thực hiện xuất file csv các khóa
    """
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListGeneration")
        unitRole = request.user.unit_role
        # Rule admin
        if unitRole == 0:
            list_generation = Generations.objects.all()
        else: # Rule quản trị cấp trường
            list_generation = Generations.objects.filter(unit=unitRole).all()
        rows = ([i+1, generation.generationName, generation.beginningYear, generation.unit] for generation, i in zip(list_generation, range(list_generation.count()))) 
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        writer.writerow(['stt', 'generationName', 'beginningYear', 'unit'])
        [writer.writerow([row[0], row[1], row[2], row[3]]) for row in rows]
        createLog(request, 'EXPORT - Khóa', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/generation/')


@login_required(login_url='/login/')
def import_page(request):
    """
    Thực hiện đọc file csv để lưu bào DB
    """
    if checkInUrl(request, 'generation') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/generationimport.html'
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
                years = Years.objects.all()
                # dict lưu "tên năm học": id - "2018-2019": 2
                dict_year = {}
                for year in years:
                    dict_year[year.yearName.lower().strip()] = year.yearID
                for i, row in df.iterrows():
                    generation = row['GenerationName']
                    yearStart = row['Year_Start']
                    # Kiểm tra nếu năm không tồn tại thì thông báo lỗi
                    if row['Year_Start'] in dict_year:
                        yearStart = dict_year[yearStart]
                    else:
                        messages.error(request,'Lỗi: Trong hệ thống không tồn tại ' + row['beginningYear'] + '.')
                        return TemplateResponse(request, template, context=context)
                    try:
                        toDatabase = Generations(generationName=generation, beginningYear_id=yearStart, unit_id=unitId)
                        toDatabase.save()
                    except (Exception) as error:
                        print(error)
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
                return TemplateResponse(request, template, context=context)
            return redirect('/adminuet/generation/')
        else:
            messages.error(request,'Lỗi: Đã xảy ra lỗi vui lòng thử lại.')
            context['lastUnitInput'] = unitInput
            return TemplateResponse(request, template, context=context)