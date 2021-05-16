from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import redirect
from django.contrib import messages
import math
from mainApp.forms import FunctionForm
from mainApp.models import Functions, create_from_DF
from mainApp.serializers.functionserializer import FunctionsSerializer
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
import pandas as pd
import csv
from django.http import HttpResponse

@login_required(login_url='/login/')
def functionPagination_page(request, num=1, limit=10):
    """
    Hiển thị trang chức năng với trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/function.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def function_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong function theo offset
        Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        functions = Functions.objects.order_by('-functionID').all()
        functionList = functions[offset:offset + limit]
        functionCount = functions.count()
        functionSerializer = FunctionsSerializer(functionList, many=True)
        page = math.ceil(functionCount/limit)
        data = {
            'data': functionSerializer.data,
            'numberOfPage': page,
        }
    createLog(request, 'VIEW - Chức năng', '')
    return Response(data)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def function_form(request, id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """

    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        if request.method == 'GET':
            # Rule admin
            if id == 0:
                functionForm = FunctionForm()
            else: # Rule quản tri cấp trường
                fun = Functions.objects.get(pk=id)
                functionForm = FunctionForm(instance = fun)
            return TemplateResponse(request, 'adminuet/functionform.html', {'form': functionForm})
        else:
            contentLog = 'UPDATE - Chức năng'
            contentMsg = 'Cập nhật thành công.'
            # Rule admin
            if id == 0:
                functionForm = FunctionForm(request.POST)
                contentLog = 'INSERT - Chức năng'
                contentMsg = 'Thêm mới thành công.'
            else: # Rule quản trị cấp trường
                fun = Functions.objects.get(pk=id)
                functionForm = FunctionForm(request.POST, instance=fun)
            if functionForm.is_valid():
                functionNameNew = functionForm['functionName'].value()
                if not Functions.objects.filter(functionName=functionNameNew):
                    functionForm.save()
                    createLog(request, contentLog, '')
                    messages.success(request, contentMsg)
                else:
                    messages.error(request, 'Vui lòng thay đổi tên chức năng. Chức năng này đã tồn tại.')
                    return redirect('/adminuet/function-form/'+str(id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/function/')

@login_required(login_url='/login/')
def function_delete(request, id):
    """
    Thực hiện xóa 1 chức năng
    """
    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        function = Functions.objects.get(pk=id)
        createLog(request, 'DELETE - Chức năng', str(function.functionName))
        function.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/function/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Thực hiện xuất file csv các chức năng
    """

    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListFunction")
        list_function = Functions.objects.all()
        rows = ([i+1, function.functionName]for function, i in zip(list_function, range(list_function.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        writer = csv.writer(response)
        writer.writerow(['stt', 'functionName'])
        [writer.writerow([row[0], row[1]]) for row in rows]
        createLog(request, 'EXPORT - Chức năng', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/function/')


@login_required(login_url='/login/')
def import_page(request):
    """Thực hiện nhập các chức năng từ file csv
    Hàm nhập từ file csv các trường stt, functionName vào model functions
    """
    if checkInUrl(request, 'function') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/functionimport.html'
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
        df = pd.read_csv(csv_file)
        create_from_DF(df=df, model=Functions, searching_cols=['functionName'])
    except (Exception) as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/function/')