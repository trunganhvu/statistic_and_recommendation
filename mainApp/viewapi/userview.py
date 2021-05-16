from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
import csv, io
import pandas as pd
from datetime import datetime
import math
from mainApp.models import CustomUser, Profiles, Roles, Role_Function, Functions, CustomUser_Function, Units, Majors, StudentGroups
from mainApp.serializers.userserializer import UserSerializer, ProfileSerializer
from mainApp.serializers.roleserializer import RoleFunctionSerializer
from mainApp.forms import CustomUserForm
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
from django.db.models import Q

"""
Hiển thị trang danh sách người dùng có trang và giới hạn bản ghi (chưa có dữ liệu)
"""
@login_required(login_url='/login/')
def userPagination_page(request, num=1, limit=10):
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/user.html', {'page': num, 'limit': limit})

"""
Lấy danh sách user theo vị trị và limit bản ghi
"""
@login_required(login_url='/login/')
@api_view(['GET'])
def user_getListForOffset(request, offset, limit):
    """
    Hàm trả về  các row trong function theo offset
    Trả về số lượng page mà chia theo limit
    """
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        unitRole = request.user.unit_role
        # get tất cả các bản ghi có trong bảng CustomUser
        if unitRole == 0:
            users = CustomUser.objects.order_by('-id').all()
        else:
            listProfileQuery = Profiles.objects.filter(major__unit=unitRole).all()
            arrayProfile = []
            for p in listProfileQuery:
                if p.user_id != None:
                    arrayProfile.append(p.user_id)
            users = CustomUser.objects.filter(pk__in=arrayProfile).order_by('-id').all()
        # get các bản ghi giới hạn từ users theo phạm vị và lấy thêm thông tin từ Roles
        userList = users[offset:offset + limit].select_related('role')
        # Biến lưu độ dài để tính số lượng tra đổ dữ liệu
        userCount = users.count()
        # Chuyển dạng queryset về json nhờ serializer rest_framework
        userSerializer = UserSerializer(userList, many=True)
        # for để gắn role.roleName cho role trong serializer
        profileDefault = [{
            "firstName": "",
            "lastName": "Chưa có thông tin",
            "email": "Chưa có thông tin",
            "MSSV": "Chưa có thông tin",
            "gender": "Chưa có thông tin",
            "birthday": "Chưa có thông tin",
            "group": "Chưa có thông tin",
            "major": "Chưa có thông tin"
        }]
        customUser_Functions = CustomUser_Function.objects.all()
        for userserializer, userlist in zip(userSerializer.data, userList):
            # Lấy dữ liệu từ khóa ngoại role từ Role_Functions
            rolefunction = Role_Function.objects.only('function').filter(role=userlist.role).select_related('function')                
            arrayRoleFunction = []
            rolefunctionSerializer = RoleFunctionSerializer(rolefunction, many=True)
            for rf, rfS in zip(rolefunction, rolefunctionSerializer.data):
                rfS['function'] = rf.function.functionName
                arrayRoleFunction.append(rf.function.functionName)

            # Lấy thêm function trong CustomUser_Function
            # Đây là nhưng function được thêm riêng biệt với từng user
            functionInUserFunction = customUser_Functions.filter(user=userlist)
            for fIUF in functionInUserFunction:
                arrayRoleFunction.append(fIUF.function.functionName)
            userserializer['functions'] = arrayRoleFunction
            
            # Lấy tên role từ Roles
            userserializer['role'] = "" if userlist.role is None else userlist.role.roleName

            # get profile của user thông qua id của user đó
            # profiles = Profiles.objects.filter(user=userlist.id).select_related('group', 'major')
            profiles = Profiles.objects.filter(user=userlist.id).select_related('group', 'major')

            if profiles.count() == 0: 
                userserializer['profile'] = profileDefault
            else:
                # sử dụng serializer tương tụ
                profileSerializer = ProfileSerializer(profiles, many=True)
                # for để gắn dữ liệu cho các trường thông tin khóa phụ
                for profileserializer, p in zip(profileSerializer.data, profiles):
                    if p.group is None:
                        profileserializer['group'] = "None"
                    else:
                        profileserializer['group'] = p.group.groupName
                    profileserializer['major'] = "None" if p.major is None else p.major.majorName
                # thêm dữ liệu trong profile của từng user vào thuộc tính 'profile'
                userserializer['profile'] = profileSerializer.data
            
        page = math.ceil(userCount/limit)
        data = {
            'data': userSerializer.data,
            'numberOfPage': page,
        }
        createLog(request, 'VIEW - Người dùng', '')
    return Response(data)

"""
Form chung cho cả Thêm mới và Sửa
Thêm mới dùng POST
Sửa dùng GET để lấy thêm dữ liệu của row hiện tại
"""
@login_required(login_url='/login/')
@api_view(['GET','POST'])
def user_form(request, id=0):

    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        if request.method == 'GET':
            if id == 0:
                userForm = CustomUserForm()
            else:
                user =  CustomUser.objects.get(pk=id)
                userForm = CustomUserForm(instance=user)
            return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm})
        else:
            contentLog = 'UPDATE - Người dùng'
            if id == 0:
                userForm = CustomUserForm(request.POST)
                contentLog = 'INSERT - Người dùng'
            else:
                user =  CustomUser.objects.get(pk=id)
                userForm = CustomUserForm(request.POST,instance=user)
            if userForm.is_valid():
                userForm.save()
                createLog(request, contentLog, '')
    except Exception as error:
        print(error)
    return redirect('/adminuet/user/')

"""
Thực hiện hiện thị và thêm mới user
"""
@login_required(login_url='/login/')
def user_form_create(request):
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        isAdminUnit = False
        unitRole = request.user.unit_role 
        if unitRole == 0:
            listRole = Roles.objects.all()
            listUnit = Units.objects.all()
            listMajor = Majors.objects.all()
            listGroup = StudentGroups.objects.all()
            dictUnits = {'0': 'Tất cả đơn vị'}
        else:
            listRole = Roles.objects.filter(~Q(roleName='Admin')).all()
            listUnit = Units.objects.filter(pk=unitRole).all()
            listMajor = Majors.objects.filter(unit=unitRole).all()
            listGroup = StudentGroups.objects.filter(generation__unit=unitRole).all()
            dictUnits = {}  
            isAdminUnit = True 
        for unit in listUnit:
            dictUnits[unit.unitID] = unit.unitName
        if request.method == 'GET':
            userForm = CustomUserForm()
            return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listRole': listRole,
                                                                        'listUnits': dictUnits, 'listMajor': listMajor, 
                                                                        'listGroup': listGroup, 'isAdminUnit': isAdminUnit})
        else:
            userForm = CustomUserForm(request.POST)
            role = request.POST['role']
            roleUnit = request.POST['roleUnit']
            username = userForm['username'].value().strip()
            password = userForm['password'].value().strip()
            majorId = request.POST['major']
            groupId = request.POST['group']
            context = {
                'username': username,
                'password': password,
                'listUnits': dictUnits,
            }
            if str(roleUnit) == 'none' or str(role) == 'none':
                messages.error(request, 'Lỗi: Vui lòng chọn các thông tin bắt buộc.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                            'context': context, 'listRole': listRole, 
                                                                            'listMajor': listMajor, 'listGroup': listGroup, 
                                                                            'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                            'majorId': majorId, 'groupId': groupId,
                                                                            'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            roleNameQuery = listRole.filter(roleID=role)
            roleNameNew = ''
            for rN in roleNameQuery:
                roleNameNew = rN.roleName
            if roleNameNew.lower() == 'sinh viên':
                if str(majorId) == 'none' or str(groupId) == 'none':
                    messages.error(request, 'Lỗi: Vui lòng chọn các thông tin cho sinh viên.')
                    return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                                'context': context, 'listRole': listRole, 
                                                                                'listMajor': listMajor, 'listGroup': listGroup, 
                                                                                'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                                'majorId': majorId, 'groupId': groupId,
                                                                                'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            if not checkInput(username, password):
                messages.error(request, 'Lỗi: Bạn đã nhập sai cú pháp. Vui lòng nhập lại.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 'context': context})
            date_joined = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            roleInRoles = Roles.objects.filter(roleID=role)[:1]
            if roleInRoles.exists():
                for r in roleInRoles:
                    if roleNameNew.lower() == 'sinh viên':
                        user = CustomUser(password=password,last_login=None, username=username, date_joined=date_joined, role_id=r.roleID)#, unit_role=roleUnit)
                        user.save()
                        userId = user.id
                        profile = Profiles(major_id=majorId, email='@mail.com', user_id=userId, firstName=' ', lastName=' ', MSSV=username, gender='Nam', birthday='2000-01-01', group_id=groupId)
                        profile.save()
                    else:
                        user = CustomUser(password=password,last_login=None, username=username, date_joined=date_joined, role_id=r.roleID, unit_role=roleUnit)
                        user.save()
                createLog(request, 'INSERT - Người dùng', username)
                messages.success(request, "Thêm mới thành công.")
            else:
                messages.error(request, 'Lỗi: Đã xảy ra lỗi.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'context': context})      
    except Exception as error:
        print(error)
        messages.success(request, "Thao tác thất bại.")
    return redirect('/adminuet/user/')

"""
Thực hiện hiển thị và cập nhật user
"""
@login_required(login_url='/login/')
def user_form_update(request, id):
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        isAdminUnit = False
        unitRole = request.user.unit_role
        if unitRole == 0:
            listRole = Roles.objects.all()
            listUnit = Units.objects.all()
            listMajor = Majors.objects.all()
            listGroup = StudentGroups.objects.all()
            dictUnits = {'0': 'Tất cả đơn vị'}
        else:
            listRole = Roles.objects.filter(~Q(roleName='Admin')).all()
            listUnit = Units.objects.filter(pk=unitRole).all()
            listMajor = Majors.objects.filter(unit=unitRole).all()
            listGroup = StudentGroups.objects.filter(generation__unit=unitRole).all()
            dictUnits = {}  
            isAdminUnit = True
        for unit in listUnit:
            dictUnits[unit.unitID] = unit.unitName
        
        if request.method == 'GET':
            user = CustomUser.objects.get(pk=id)
            role = user.role.roleID
            
            profileUser = Profiles.objects.filter(user=id).first()
            # roleUnit = user.unit_role
            if profileUser is None:
                roleUnit = "None"
                majorId = "None"
                groupId = "None"
            else: 
                roleUnit = profileUser.major.unit.unitID
                majorId = profileUser.major.majorID
                groupId = profileUser.group.groupID
            userForm = CustomUserForm(instance=user)
            return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                        'roleUnit': roleUnit, 'listMajor': listMajor, 
                                                                        'listGroup': listGroup, 'isAdminUnit': isAdminUnit,
                                                                        'majorId': majorId, 'groupId': groupId,
                                                                        'listRole': listRole, 'roleId': role,})
        else:
            userForm = CustomUserForm(request.POST)
            role = request.POST['role']
            roleUnit = request.POST['roleUnit']
            username = userForm['username'].value().strip()
            password = userForm['password'].value().strip()
            majorId = request.POST['major']
            groupId = request.POST['group']
            date_joined = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context = {
                'username': username,
                'password': password,
                'listUnits': dictUnits,
            }
            if str(roleUnit) == 'none' or str(role) == 'none':
                messages.error(request, 'Lỗi: Vui lòng chọn các thông tin bắt buộc.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                            'context': context, 'listRole': listRole, 
                                                                            'listMajor': listMajor, 'listGroup': listGroup, 
                                                                            'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                            'majorId': majorId, 'groupId': groupId,
                                                                            'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            if not checkInput(username, password):
                messages.error(request, 'Lỗi: BcheckInputạn đã nhập sai cú pháp. Vui lòng nhập lại.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                            'context': context, 'listRole': listRole, 
                                                                            'listMajor': listMajor, 'listGroup': listGroup, 
                                                                            'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                            'majorId': majorId, 'groupId': groupId,
                                                                            'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            if CustomUser.objects.exclude(pk=id).filter(username=username).exists():
                messages.error(request, 'Lỗi: Tên đăng nhập đã tồn tại. Vui lòng nhập lại.')
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                            'context': context, 'listRole': listRole, 
                                                                            'listMajor': listMajor, 'listGroup': listGroup, 
                                                                            'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                            'majorId': majorId, 'groupId': groupId,
                                                                            'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            roleNameQuery = listRole.filter(roleID=role)
            roleNameNew = ''
            for rN in roleNameQuery:
                roleNameNew = rN.roleName
            if roleNameNew.lower() == 'sinh viên':
                if str(majorId) == 'none' or str(groupId) == 'none':
                    messages.error(request, 'Lỗi: Vui lòng chọn các thông tin cho sinh viên.')
                    return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'listUnits': dictUnits, 
                                                                                'context': context, 'listRole': listRole, 
                                                                                'listMajor': listMajor, 'listGroup': listGroup, 
                                                                                'isAdminUnit': isAdminUnit, 'roleId': role,
                                                                                'majorId': majorId, 'groupId': groupId,
                                                                                'roleUnit': roleUnit, 'isAdminUnit': isAdminUnit})
            roleInRoles = Roles.objects.filter(roleID=role)[:1]
            if roleInRoles.exists():
                for r in roleInRoles:
                    if roleNameNew.lower() == 'sinh viên':
                        CustomUser.objects.filter(id=id).update(password=password,last_login=None, username=username, date_joined=date_joined, role_id=r.roleID, unit_role=None)
                        Profiles.objects.filter(user_id=id).update(major_id=majorId, group_id=groupId)
                    else:
                        CustomUser.objects.filter(id=id).update(password=password,last_login=None, username=username, date_joined=date_joined, role_id=r.roleID, unit_role=roleUnit)
                createLog(request, 'UPDATE - Người dùng', username)
                messages.success(request, "Cập nhật thành công.")
            else:
                messages.error(request, "Thao tác thất bại.")
                return TemplateResponse(request, 'adminuet/userform.html', {'form': userForm, 'context': context})
            return redirect('/adminuet/user/')
    except Exception as error:
        print(error)
        messages.error(request, "Thao tác thất bại.")
        return redirect('/adminuet/user/')

"""
Kiểm tra nhập của user
"""
def checkInput(username, password):
    if username == ' ' or password == ' ' or '<' in username or '<' in password or '%' in username or '%' in password or '>' in username or '>' in password:
        return False
    return True

"""
Thưc hiện xóa user
"""
@login_required(login_url='/login/')
def user_delete(request, id):
    """
    Đưa id vào để xóa row có id
    """
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        Profiles.objects.filter(user_id=id).delete()
        user = CustomUser.objects.get(pk=id)
        createLog(request, 'DELETE - Người dùng', user.username)
        user.delete()
        messages.success(request, "Xóa thành công.")
    except Exception as error: 
        print(error)
    return redirect('/adminuet/user/')

"""
Xuất danh sách user ra file csv
"""
@login_required(login_url='/login/')
def export_page(request):
    """
    Thuộc tính của file csv: stt, roleName, roleDescription
    """
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    try:
        nameFileExport = 'attachment; filename="{}.csv"'.format("ListUser")
        # get tất cả các bản ghi có trong bảng CustomUser
        users = CustomUser.objects.all().select_related('role')
        # for để gắn role.roleName cho role trong serializer
        for user, i in  zip(users, range(users.count())):
            # get profile của user thông qua id của user đó
            profiles = Profiles.objects.filter(user=user.id).select_related('group', 'major')
            mssv = ' '
            firstname = ' '
            lastname = ' '
            email = ' '
            groupname = ' '
            majorname = ' '
            for profile in profiles:   
                mssv = profile.MSSV
                firstname = profile.firstName
                lastname = profile.lastName
                email = profile.email
                groupname =profile.group.groupName
                majorname = profile.major.majorName
            rows = str(i), user.username, user.password, user.role.roleName, mssv, firstname, lastname, email, groupname, majorname, user.date_joined.strftime("%d/%m/%Y, %H:%M:%S")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = nameFileExport
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response)
        writer.writerow(['stt', 'username','password','role','mssv','firstname','lastname','email','groupname','majorname','datejoin'])
        createLog(request, 'EXPORT - Người dùng', '')
        return response 
    except Exception as error: 
        print(error)
    return redirect('/adminuet/user/')       

"""
Thực hiện hiển thị và phần quyền đặc biệt cho người dùng
"""
@login_required(login_url='/login/')
def user_permissions(request):
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'POST':
        functions = Functions.objects.all().only('functionName')
        listUserSubmit = request.POST.getlist('userID')
        context = {
            'functions': functions,
        }
        users = []
        listFunctionInUser = []
        customUser_Function = CustomUser_Function.objects.all()
        # lặp theo từng user mà người dungf nhập vào theo id
        for user in listUserSubmit:
            userID = int(user)
            # lấy toàn bộ thông tin theo Id của 1 người dùng
            listUserInDB = CustomUser.objects.get(pk=userID)
            # lấy các function của user thông qua role của Role_Function
            listFunctionUserInDB = Role_Function.objects.filter(role=listUserInDB.role.roleID)
            # Thêm vào array 1 username của 1 user
            users.append(listUserInDB.username)
            # lấy ra tên các function đưa vào mảng - không đưa tên đã tồn tại trong array
            for functionInDB in listFunctionUserInDB:
                # Kiểm tra đã tồn tại trong mảng chưa
                if not functionInDB.function.functionName in listFunctionInUser:
                    listFunctionInUser.append(functionInDB.function.functionID)
            # lấy ra tên function trong bảng CustomUser_Function - đối với người dùng có thêm function riêng biệt
            listFunctionInDBExtra = customUser_Function.filter(user=userID)
            # Nếu có người dùng đó có functiong riêng biệt thì append functionID vào array
            for functionExtra in listFunctionInDBExtra:
                listFunctionInUser.append(functionExtra.function.functionID)
        
        # thêm thuộc tính vào context
        context['currentFunctions'] = listFunctionInUser
        context['users'] = users
    return TemplateResponse(request, 'adminuet/userpermission.html', context=context)

"""
Thực hiện hiện thị và update quyền cho người dùng
"""
@login_required(login_url='/login/')
def user_permissions_update(request):
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'POST':
        listUserSubmit = request.POST.getlist('user')
        listFunctionSubmit = request.POST.getlist('function')
        listUserFromDatabase = CustomUser.objects.all()
        functions = Functions.objects.all().only('functionName')
        context = {
            'functions': functions,
            'currentFunctions': listFunctionSubmit,
            'users': listUserSubmit,
        }
        arrayUserToUpdate = []
        if len(listUserSubmit) == 0 or len(listFunctionSubmit) == 0:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
            return TemplateResponse(request, 'adminuet/userpermission.html', context=context)
        for user in listUserSubmit:
            # Kiểm tra dữ liệu gửi lên nếu không tồn tại thì báo lỗi 
            if listUserFromDatabase.filter(username=user).exists():
                userInfo = listUserFromDatabase.filter(username=user)
                arrayUserToUpdate.append(userInfo)
            else:
                messages.error(request, 'Đã có lỗi với tên người dùng.')
                return TemplateResponse(request, 'adminuet/userpermission.html', context=context)
            # kết thúc đã có array các username thỏa mãn không lỗi gì
        # print(arrayUserToUpdate)

        arrayFunctionToUpdate = []
        for function in listFunctionSubmit:
            # Kiểm tra dữ liệu gửi lên nếu không tồn tại thì báo lỗi 
            if functions.filter(functionID=function).exists():
                arrayFunctionToUpdate.append(functions.get(pk=function).functionID)
            else:
                messages.error(request, 'Đã có lỗi với chức năng đã lựa chọn.')
                return TemplateResponse(request, 'adminuet/userpermission.html', context=context)
            # đã có 1 array các id của function

        # print(arrayFunctionToUpdate)
        customUser_Function = CustomUser_Function.objects.all()
        role_functions = Role_Function.objects.all()
        for user in arrayUserToUpdate:
            userId = ''
            for u in user:
                # userId là id duy nhất 1 user
                userId = u.id
                # lấy ra roleId của 1 user
                roleInUser = u.role.roleID
            # Lây ra toàn bộ chức năng của 1 role
            functionsForOneUser = role_functions.filter(role=roleInUser).select_related('function')
            # những function có trong Role
            arrayFunctionUserInDB = []
            for functionForOneUser in functionsForOneUser:
                arrayFunctionUserInDB.append(functionForOneUser.function.functionID)
            
            # Xóa luôn các user có trong bảng nếu có thay đổi sau đó ghi lại
            # Nếu không ghi lại thì user đó đã bị bỏ các function riêng biệt
            CustomUser_Function.objects.filter(user=userId).delete()
            # Duyệt từng phần tử id trong mảng array function mà user nhập vào
            # Nếu 1 phần tử không có trong array function của role (role lấy trong user)
            for functionInArray in arrayFunctionToUpdate:
                # Kiểm tra nhưng 1 function từ người dùng có trong những function của Role không
                if not functionInArray in arrayFunctionUserInDB:
                    
                    # tạo ra bản ghi trong bảng CustomUser_Function
                    customUser_Function = CustomUser_Function(function_id=functionInArray, user_id=userId)
                    customUser_Function.save()
                    createLog(request, 'UPDATE - Người dùng', '')
                    messages.success(request, "Cập nhật thành công.")
    return redirect('/adminuet/user/')

"""
Đọc file csv để nhập vào DB
"""
@login_required(login_url='/login/')
def import_page(request):
    """
    Thuộc tính của file csv 
    """
    if checkInUrl(request, 'user') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    template = 'adminuet/userimport.html'
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
        customUsers = CustomUser.objects.all()
        roles = Roles.objects.all()
        for i, row in df.iterrows():
            username = row['username']
            password = row['password']
            rolename = row['role']
            date_joined = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # check username đã tồn tại chưa
            if customUsers.filter(username=username).exists():
                messages.error(request,'Đã tồn tại username.')
                return TemplateResponse(request, template)
            else:
                # check rolename có tồn tại hay không
                if not roles.filter(roleName=rolename).exists():
                    messages.error(request, str(rolename) + ' không tồn tại trong hệ thống.')
                    return TemplateResponse(request, template)
                else:
                    role = roles.filter(roleName=rolename)
                    for r in role:
                        user = CustomUser(password=password, username=username, date_joined=date_joined,is_active=True, role_id=r.roleID)
                        user.save()
    except (Exception) as error:
        print(error)
        messages.error(request,'Lỗi: Dữ liệu không đúng định dạng.')
        return TemplateResponse(request, template)
    return redirect('/adminuet/role/')