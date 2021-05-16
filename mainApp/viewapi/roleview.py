from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import pandas as pd
from mainApp.forms import RoleForm
from mainApp.models import Roles, update_from_DF, create_from_DF, Role_Function, Functions
from mainApp.serializers.roleserializer import RoleSerializer, RoleFunctionSerializer
import csv, io
import math
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
import html
from mainApp.viewapi.logs import createLog

@login_required(login_url='/login/')
def rolePagination_page(request, num=1, limit=10):
    """
    Hiển thị trang danh sách các vai trò có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/role.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def role_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong role theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        role_functions = Role_Function.objects.order_by('-ID').all()[offset:offset + limit].select_related('function', 'role')
        roleFunctionSerializer = RoleFunctionSerializer(role_functions, many=True)
        roles = Roles.objects.order_by('-roleID').all()
        roleResult = roles[offset:offset + limit]

        page = math.ceil(roles.count()/limit)
        roleSerializer = RoleSerializer(roleResult, many=True)
        data = {
            'data': roleSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Vai trò', '')
        return Response(data)

def check_string_safe(text):
    """
    Kiểm tra các ký tự đặc biệt
    """
    listCharacterRick = ['<', '>', '/', '?', '%', '"', '{', '}', '\\', '&', '(', ')', '%', ':', ';', '|']
    for character in text:
        if character in listCharacterRick:
            return False
    return True

@login_required(login_url='/login/')
def role_form_new(request):
    """
    Thực hiện tạo một role mới
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    functions = Functions.objects.all()
    roles = Roles.objects.all()
    context = {
        'functions': functions
    }
    if request.method == 'POST':
        roleInput = request.POST['roleName'] 
        roleDescription = request.POST['roleDescription']
        listFunctionInput = request.POST.getlist('function')
        # Kiểm tra có gửi khoảng trắng không
        if roleInput.strip() == "":
            messages.error(request, 'Vui lòng nhập tên vai trò.')
            return TemplateResponse(request, 'adminuet/roleform.html', context=context)
        # Kiểm tra trong đoạn input người dùng có kèm mã độc không
        if not check_string_safe(roleInput):
            messages.error(request, 'Vui lòng thay đổi tên vai trò.')
            return TemplateResponse(request, 'adminuet/roleform.html', context=context)
        # Kiểm tra input đã tồn tại không - Nếu không tồn tại mới cho tạo
        if roles.filter(roleName=roleInput).exists():
            messages.error(request, 'Vui lòng thay đổi tên vai trò.')
            context['roleNameLast'] = roleInput
            return TemplateResponse(request, 'adminuet/roleform.html', context=context)
        if len(listFunctionInput) == 0:
            messages.error(request, 'Vui lòng chọn lại chức năng.')
            context['roleNameLast'] = roleInput
            return TemplateResponse(request, 'adminuet/roleform.html', context=context)
        for item in listFunctionInput:
            # Kiểm tra id mà người dùng gửi có tồn tại không 
            if not functions.filter(functionID=item).exists():
                messages.error(request, 'Vui lòng thay đổi.')
                context['roleNameLast'] = roleInput
                return TemplateResponse(request, 'adminuet/roleform.html', context=context)
        # Thực hiện kiểm tra mô tả khác rỗng và gán giá trị mặc định nếu cần
        if roleDescription == '':
            roleDescription = 'Chưa có thông tin'
        else:
            html.escape(roleDescription)
        # Thực hiện ghi vào csdl 
        try:
            role = Roles(roleName=roleInput, roleDescription=roleDescription)
            role.save()
            role_id = role.roleID
            # for 1 lần nữa để chắc chắc tất cả id function đều tồn tại
            for item in listFunctionInput:
                function = Role_Function(role_id=role_id, function_id=item)
                function.save()
            createLog(request, 'INSERT - Vai trò', '')
            messages.success(request, "Thêm mới thành công.")
            return redirect('/adminuet/role/')
        except (Exception) as error:
            print(error)
            messages.error(request,'Đã xảy ra lỗi vui lòng thử lại.')
            return TemplateResponse(request, 'adminuet/roleform.html', context=context)        
    return TemplateResponse(request, 'adminuet/roleform.html', context=context)

@login_required(login_url='/login/')
def role_form_update_new(request, id):
    """
    Thực hiện update role
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        role_function = Role_Function.objects.filter(role=id).select_related('role', 'function')
        functions = Functions.objects.all()
        rolename = ''
        roleDescription = ''
        functionOfRole = []
        for rf in role_function:
            rolename = rf.role.roleName
            roleDescription = rf.role.roleDescription
            functionOfRole.append(rf.function.functionID)
        context = {
            'functions': functions,
            'roleNameLast': rolename,
            'roleDescriptionLast': roleDescription,
            'functionOfRole': functionOfRole,
        }
        if request.method == 'POST':
            roleInput = request.POST['roleName'] 
            roleDescription = request.POST['roleDescription']
            listFunctionInput = request.POST.getlist('function')
            # Kiểm tra có gửi khoảng trắng không
            if roleInput.strip() == "":
                messages.error(request, 'Vui lòng nhập tên vai trò.')
                return TemplateResponse(request, 'adminuet/roleform.html', context=context)
            # Kiểm tra trong đoạn input người dùng có kèm mã độc không
            if not check_string_safe(roleInput):
                messages.error(request, 'Vui lòng thay đổi tên vai trò.')
                return TemplateResponse(request, 'adminuet/roleform.html', context=context)
            # Kiểm tra input đã tồn tại không - Nếu không tồn tại mới cho tạo
            if Roles.objects.filter(roleName=roleInput).exists() and roleInput != rolename:
                messages.error(request, 'Vui lòng thay đổi tên vai trò.')
                context['roleNameLast'] = roleInput
                return TemplateResponse(request, 'adminuet/roleform.html', context=context)
            for item in listFunctionInput:
                # Kiểm tra id mà người dùng gửi có tồn tại không 
                if not functions.filter(functionID=item).exists():
                    messages.error(request, 'Vui lòng thay đổi.')
                    context['roleNameLast'] = roleInput
                    return TemplateResponse(request, 'adminuet/roleform.html', context=context)
            # Thực hiện kiểm tra mô tả khác rỗng và gán giá trị mặc định nếu cần
            if roleDescription == '':
                roleDescription = 'Chưa có thông tin'
            else:
                html.escape(roleDescription)
            try:
                # Update lại roleName ở bên Roles
                role = Roles.objects.get(pk=id)
                role.roleName = roleInput
                role.roleDescription = html.escape(roleDescription)
                role.save()
                role_id = role.roleID
                # Xoá trước hết các bản ghi có role_id đó
                Role_Function.objects.filter(role=role_id).delete()

                # for 1 lần nữa để chắc chắc tất cả id function đều tồn tại
                for item in listFunctionInput:
                    function = Role_Function(role_id=role_id, function_id=item)
                    function.save()
                createLog(request, 'UPDATE - Vai trò', '')
                messages.success(request, "Cập nhật thành công.")
                return redirect('/adminuet/role/')
            except (Exception) as error:
                print(error)
                messages.error(request,'Đã xảy ra lỗi vui lòng thử lại.')
                return TemplateResponse(request, 'adminuet/roleform.html', context=context)    
        return TemplateResponse(request, 'adminuet/roleform.html', context=context)
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
        return redirect('/adminuet/role/')


# @login_required(login_url='/login/')
# def role_form(request, id=0):
#     """
#     Form thêm mới dùng tên vai trò và mô tả để biết các chức năng của vai trò
#     """
#     if checkInUrl(request, 'role') is False:
#         listFunction = request.user.list_function()
#         return HttpResponseRedirect(reverse(listFunction[0]))
#     functions = Functions.objects.all()
#     roles = Roles.objects.all()
#     context = {
#         'functions': functions
#     }
#     dict_functionToID = {}
#     for f in functions:
#         dict_functionToID[f.functionName] = f.functionID
#     if request.method == 'POST':
#         roleInput = request.POST['roleName'] 
#         listFunctionInput = request.POST.getlist('function')
#         for rowRole in roles:
#             # Kiểm tra tên mới nhập có thay đổi không và kiểm tra đã tồn tại không
#             if roleInput.strip().lower() == rowRole.roleName.lower():
#                 messages.error(request, 'Vui lòng thay đổi tên vai trò.')
#                 context['roleNameLast'] = roleInput
#                 return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#         # Kiểm tra độ dài của chuỗi checkbox nếu = 0  thì chưa tích và báo là lựa chọn
#         if len(listFunctionInput) == 0:
#             messages.error(request, 'Vui lòng chọn lại chức năng.')
#             context['roleNameLast'] = roleInput
#             return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#         else: 
#             # Ghép các checkbox thành string để insert vào roleDesctiption
#             listToStringRole = ','.join(map(str, listFunctionInput))
#             try:
#                 roleCreate = Roles.objects.create(roleName=roleInput, roleDescription=listToStringRole)               
#                 roleNew = Roles.objects.filter(roleName=roleInput).values('roleID')[:1]
#                 for row in roleNew:
#                     roleIDNew = row['roleID']
#                 # print(roleIDNew, type(roleIDNew))
#                 for function in listFunctionInput:
#                     listRole = Roles.objects.all()
#                     # for r in listRole:
#                     #     print(r.roleID, r.roleName)
#                     role_function = Role_Function(role=roleIDNew, function=dict_functionToID[function])
#                     role_function.save()
#                 return redirect('/adminuet/role/')
#             except (Exception) as error:
#                 print(error)
#                 messages.error(request,'Đã xảy ra lỗi vui lòng thử lại.')
#                 return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#     return TemplateResponse(request, 'adminuet/roleform.html', context=context)

# @login_required(login_url='/login/')
# def role_form_update(request, id):
#     if checkInUrl(request, 'role') is False:
#         listFunction = request.user.list_function()
#         return HttpResponseRedirect(reverse(listFunction[0]))
#     try:
#         roles = Roles.objects.get(pk=id)
#         functions = Functions.objects.all()
#         context = {
#             'functions': functions,
#             'roleNameLast': roles,
#             'functionOfRole': roles.roleDescription
#         }
#         if request.method == 'POST':
#             roleInput = request.POST['roleName'] 
#             listFunctionInput = request.POST.getlist('function')
#             rolesList = Roles.objects.all()
#             for rowRole in rolesList:
#                 # Kiểm tra tên mới nhập có thay đổi không và kiểm tra đã tồn tại không
#                 if roleInput.strip().lower() == rowRole.roleName.lower() and roleInput.strip().lower() != roles.roleName.lower():
#                     messages.error(request, 'Vui lòng thay đổi tên vai trò.')
#                     context['roleNameLast'] = roles
#                     return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#             # Kiểm tra độ dài của chuỗi checkbox nếu = 0  thì chưa tích và báo là lựa chọn 
#             if len(listFunctionInput) == 0:
#                 messages.error(request, 'Vui lòng chọn lại chức năng.')
#                 context['roleNameLast'] = roles
#                 return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#             roles.roleName = roleInput
#             # Ghép các checkbox thành string để insert vào roleDesctiption
#             listToStringRole = ','.join(map(str, listFunctionInput))
#             roles.roleDescription = listToStringRole
#             roles.save()
#             return redirect('/adminuet/role/')
#         return TemplateResponse(request, 'adminuet/roleform.html', context=context)
#     except (Exception) as error:
#         print(error)
#     return redirect('/adminuet/role/')

@login_required(login_url='/login/')
def role_delete(request, id):
    """
    Thực hiện xóa role
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        role = Roles.objects.get(pk=id)
        createLog(request, 'DELETE - Vai trò', str(role.roleName))
        role.delete()
        messages.success(request, "Xóa thành công.")
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/role/')

@login_required(login_url='/login/')
def export_page(request):
    """
    xuất danh sách các role ra file csv
    Thuộc tính của file csv: stt, roleName, roleDescription
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListRole")
        list_role = Roles.objects.all()
        rows = ([i+1, role.roleName, role.roleDescription] for role, i in zip(list_role, range(list_role.count())))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['stt', 'roleName', 'roleDescription'])
        [writer.writerow([row[0], row[1], row[2] ]) for row in rows]
        createLog(request, 'EXPORT - Vai trò', '')
        return response
    except (Exception) as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/role/')


@login_required(login_url='/login/')
def import_page(request):
    """
    Thực hiện đọc file csv để nhập vào DB (không sử dụng)
    Thuộc tính của file csv roleName, roleDescription
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/roleimport.html'
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
        functions = Functions.objects.all()
        # List các roleName để so sanh sự tồn tại
        list_function = [] 
        for function in functions:
            list_function.append(function.functionName)
        for i, row in df.iterrows():
            roleDes = row['roleDescription']
            # Phân tách các chuỗi string bời dấu , vào list_function
            listToStringRole = roleDes.split(",")
            for itemFunction in listToStringRole:
                # Nếu itemFunction không có trong list_function thì báo lỗi luôn
                if not itemFunction in list_function:
                    messages.error(request,'Lỗi: Trong hệ thống không tồn tại chức năng ' + itemFunction +'.')
                    return TemplateResponse(request, template)
        # Thực hiện ghi dữ liệu 
        create_from_DF(df=df, model=Roles, searching_cols=['roleName', 'roleDescription'])           
    except (Exception) as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/role/')


@login_required(login_url='/login/')
def import_page_new(request):
    """
    Thực hiện đọc file csv để nhập vào DB
    Thuộc tính của file csv stt, roleName, roleDescription, functions
    """
    if checkInUrl(request, 'role') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/roleimport.html'
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
        functions = Functions.objects.all()
        roles = Roles.objects.all()
        # List các functionName để so sanh sự tồn tại
        list_function = {} 
        for function in functions:
            list_function[function.functionName] = function.functionID
        for i, row in df.iterrows():
            roleName = row['roleName']
            roleDescription = row['roleDescription']
            functionInput = row['funcitons']
            if roles.filter(roleName=roleName).exists():
                messages.error(request,'Lỗi: Tên vai trò đã trùng.')
                return TemplateResponse(request, template)
            else:
                role = Roles(roleName=roleName, roleDescription=roleDescription)
                role.save()
                roleIdNew = role.roleID
                listFunctionInFile = functionInput.split(", ")
                for itemFunction in listFunctionInFile:
                    # Nếu itemFunction không có trong list_function thì báo lỗi luôn
                    if not itemFunction in list_function:
                        messages.error(request,'Lỗi: Trong hệ thống không tồn tại chức năng ' + itemFunction +'.')
                        return TemplateResponse(request, template)
                    else:
                        role_function = Role_Function(role_id=roleIdNew, function_id=list_function[itemFunction])
                        role_function.save()
          
    except (Exception) as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/role/')