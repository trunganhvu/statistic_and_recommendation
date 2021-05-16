from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
import csv, io
from mainApp.models import update_from_DF, create_from_DF, Echo, StudentGroups, Generations, Units
from mainApp.forms import GroupForm
from mainApp.serializers.groupserializer import GroupSerializer
import math
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
from django.http import HttpResponse

@login_required(login_url='/login/')
def groupPagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách các lớp có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/group.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def group_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong major theo offset
        Trả về số lượng page mà chia theo limit group
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        # Rule admin
        if unitRole == 0:
            groups = StudentGroups.objects.order_by('-groupID').all()
        else: # Rule quản trị cấp trường
            groups = StudentGroups.objects.filter(generation__unit=unitRole).order_by('-groupID').all()
        groupList = groups[offset:offset + limit].select_related('generation')
        groupCount = groups.count()
        groupSerializer = GroupSerializer(groupList, many = True)
        page = math.ceil(groupCount/limit)
        for group, row in zip(groupList, groupSerializer.data):
            row['generation'] = group.generation.generationName + ' - ' + group.generation.unit.unitName
        data = {
            'data': groupSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Lớp', '')
        return Response(data)

@login_required(login_url='/login/')
@api_view(['GET','POST'])
def group_form(request, group_id=0):
    """
    Form chung cho cả Thêm mới và Sửa
    Thêm mới dùng POST
    Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        unitRole = request.user.unit_role
        listGeneration = Generations.objects.filter(unit=unitRole)
        if request.method == 'GET':
            if group_id == 0:
                groupForm = GroupForm()
            else: 
                group = StudentGroups.objects.get(pk=group_id)
                groupForm = GroupForm(instance=group)
            return TemplateResponse(request, 'adminuet/groupform.html', {'form': groupForm, 'listGeneration': listGeneration, 'unitRole': unitRole})
        else:
            contentLog = 'UPDATE - Lớp'
            contentMsg = 'Cập nhật thành công.'
            if group_id == 0:
                groupForm = GroupForm(request.POST)
                contentLog = 'INSERT - Lớp'
                contentMsg = 'Thêm mới thành công.'
            else:
                group = StudentGroups.objects.get(pk=group_id)
                groupForm = GroupForm(request.POST, instance=group)
            if groupForm.is_valid():
                groupNameNew = groupForm['groupName'].value()
                generation = groupForm['generation'].value()
                if not checkValueExist(groupNameNew, generation):
                    groupForm.save()
                    createLog(request, contentLog, str(groupNameNew))
                    messages.success(request, contentMsg)
                else: 
                    messages.error(request, 'Vui lòng thay đổi thông tin. Ngành đào tạo này đã tồn tại.')
                    return redirect('/adminuet/group-form/'+str(group_id))
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/group/')

def checkValueExist(groupname, generation):
    """
    Kiểm tra tên lớp đã tồn tại trong khóa
    """
    if StudentGroups.objects.filter(groupName=groupname, generation=generation).exists():
        return True

@login_required(login_url='/login/')
def group_delete(request, group_id):
    """
    Xóa một lớp
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        group = StudentGroups.objects.get(pk=group_id)
        createLog(request, 'DELETE - Lớp', group.groupName)
        group.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/group/')


@login_required(login_url='/login/')
def export_page(request):
    """
    Thực hiện xuất danh sách các lớp ra file csv
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListGroup")
        unitRole = request.user.unit_role
        if unitRole == 0:
            list_group = StudentGroups.objects.all()
        else:
            list_group = StudentGroups.objects.filter(generation__unit=unitRole).all()
        rows = ([i+1, group.groupName, group.generation] for group, i in zip(list_group, range(list_group.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['stt', 'groupName', 'generation'])
        [writer.writerow([row[0], row[1], row[2] ]) for row in rows]
        createLog(request, 'EXPORT - Lớp', '')
        return response
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/group/')

@login_required(login_url='/login/')
def import_page(request):
    """
    Các thuộc tính trong file csv Group, Generation
    Generation ví dụ là K52
    """
    if checkInUrl(request, 'group') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/groupimport.html'
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
                context['lastUnitInput'] = unitInput
                messages.error(request,'Lỗi: Chưa chọn tệp dữ liệu.')
                return TemplateResponse(request, template, context=context)
            if not csv_file.name.endswith('.csv'):
                context['lastUnitInput'] = unitInput
                messages.error(request,'Lỗi: Sai định dạng tệp. Vui lòng chọn lại tệp')
                return TemplateResponse(request, template, context=context)
            try:
                df = pd.read_csv(csv_file)
                
                for i, row in df.iterrows():
                    groupName = row['Group']
                    generation = row['Generation']
                    generartionInDB = Generations.objects.filter(generationName=generation)
                    for g in generartionInDB:
                        generationUnit = g.unit.unitID
                        generation_id = g.generationID
                        if generationUnit == int(unitInput):
                            try:
                                toDatabase = StudentGroups(groupName=groupName, generation_id=generation_id)
                                toDatabase.save()
                            except (Exception) as error:
                                print(error)
            except (Exception) as error:
                print(error)
                messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
                return TemplateResponse(request, template, context=context)
            return redirect('/adminuet/group/')