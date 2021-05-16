from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.http import HttpResponseRedirect, HttpResponse
from mainApp.models import CustomUser, Roles, Profiles, StudentGroups, Majors, Units, Generations
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.response import TemplateResponse
from django.urls import reverse
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_page(request):
    """
    Hiển thị trang đăng nhập
    """
    return TemplateResponse(request, 'student/login.html')

def user_login(request):
    """
    Nhận request và xứ lý username và password người dùng nhập để xác minh
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            if username.strip() == "" or password.strip() == "":
                messages.error(request, 'Hãy nhập đầy đủ thông tin.')
                return TemplateResponse(request, 'student/login.html')
            users = get_user_model()
            user = users.objects.filter(username=username, password=password).first()
            # check_login(username, password)
            if user:
                login(request, user)
                listFunction = user.list_function()
                if len(listFunction) > 0:
                    return HttpResponseRedirect(reverse(listFunction[0]))
                else:
                    return HttpResponseRedirect('/')
            else:
                context = {
                    'username': username
                }
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu sai.')
                return TemplateResponse(request, 'student/login.html', context=context)
        else:
            return TemplateResponse(request, 'student/login.html')

@login_required(login_url='/login/')
def user_logout(request):
    """
    Hàm logout ra khỏi tài khoản nếu đang ở trang thái login thì mới cho login
    """
    if request.user.is_authenticated:
        logout(request)
        return redirect('/')
    else:
        return TemplateResponse(request, 'student/login.html')

def check_login(username, password):
    """
    Check LDAP
    """

    return False

def user_login2(request):
    """
    Nhận request và xứ lý username và password người dùng nhập để xác minh có LDAP
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    else:
        if request.method == 'POST':
            username = request.POST.get('username').strip()
            password = request.POST.get('password')
            if username.strip() == "" or password.strip() == "" or len(password) > 30:
                messages.error(request, 'Hãy nhập đầy đủ thông tin.')
                context = {
                    'username': username
                }
                return TemplateResponse(request, 'student/login.html', context=context)
            users = get_user_model()
            user = users.objects.filter(username=username).first()
            # Nếu tên đăng nhập có tổn tại trong DB
            if user:
                # Nếu mất khẩu nhập vào giống mật khẩu lấy ra thì login thành công
                if user.password == password:
                    login(request, user)
                    listFunction = user.list_function()
                    if len(listFunction) > 0:
                        return HttpResponseRedirect('/adminuet/profile/')
                        # return HttpResponseRedirect(reverse(listFunction[0]))
                    else:
                        return HttpResponseRedirect('/')
                # Không phải mật khẩu lưu ở DB thì check LDAP
                else:
                    if check_login(username, password):
                        login(request, user)

                        listFunction = user.list_function()
                        if len(listFunction) > 0:
                            return HttpResponseRedirect('/adminuet/profile/')
                            # return HttpResponseRedirect(reverse(listFunction[0]))
                        else:
                            return HttpResponseRedirect('/')
                    else:
                        context = {
                            'username': username
                        }
                        messages.error(request, 'Tên đăng nhập hoặc mật khẩu sai.')
                        return TemplateResponse(request, 'student/login.html', context=context)
            # SV lần đầu không có trong hệ thống, kiểm tra LDAP
            elif check_login(username, password):
                # TODO thêm với DB
                role = Roles.objects.filter(roleName="Sinh viên").first()
                roleId = role.roleID
                createUser = CustomUser(password='password',
                                        last_login=None,
                                        username=username,
                                        date_joined=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        role_id=roleId,
                                        is_active=True,
                                        unit_role=None)
                createUser.save()

                mssv = username.split("@")[0]
                inProfiles = Profiles.objects.filter(MSSV=mssv)
                
                isExistInProfiles = inProfiles.exists()
                if isExistInProfiles:
                    inProfiles.update(user_id=createUser.id)
                    login(request, createUser)
                    return HttpResponseRedirect('/adminuet/profile/')

                createProfile = Profiles(firstName=" ",
                                        lastName="",
                                        email="@email.com",
                                        MSSV=mssv,
                                        gender="Nam",
                                        birthday="2000-01-01",
                                        group=None,
                                        major=None,
                                        user_id=createUser.id)
                createProfile.save()

                login(request, createUser)
                return HttpResponseRedirect('/info-first/')
            else:
                context = {
                    'username': username
                }
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu sai.')
                return TemplateResponse(request, 'student/login.html', context=context)
        else:
            return TemplateResponse(request, 'student/login.html')

@login_required(login_url='/login/')
def first_form(request):
    """
    Form nhập thông tin tên, năm sinh và trường cho sinh viên lần đầu
    """
    profile = Profiles.objects.filter(user=request.user.id).first()
    userMajor = profile.major
    userGroup = profile.group

    # major = null và group = null
    if userMajor is None and userGroup is None:
        units = Units.objects.all()
        if request.method == 'GET':
            context = {
                'units': units
            }
            return TemplateResponse(request, 'adminuet/firstform.html', context=context)
        else:
            userId = request.user.id
            lastName = ''
            firstName = ''
            birthday = ''
            unit = ''
            lastName = request.POST.get('lastName')
            firstName = request.POST.get('firstName')
            birthday = request.POST.get('birthday')
            unit = request.POST.get('unit')

            checkExistProfile = Profiles.objects.filter(user=userId).exists()
            if validate_first_form(unit, lastName, firstName, birthday):
                # Update
                if checkExistProfile:
                    Profiles.objects.filter(user=userId).update(lastName=lastName,
                                                                firstName=firstName,
                                                                birthday=birthday)
                    request.session['unitID'] = unit
                    return HttpResponseRedirect('/info-second/')
                mes = "Thao tác thất bại."
            mes = "Nhập thông tin chính xác."
            context = {
                'unit': unit,
                'units': units,
                'lastName': lastName,
                'firstName': firstName,
                'birthday': birthday
            }
            messages.error(request, mes)
            return TemplateResponse(request, 'adminuet/firstform.html', context=context)
    # major != null và group = null -> cần thêm group
    elif userMajor is not None and userGroup is None:
        unitId = Majors.objects.get(pk=userMajor.majorID).unit.unitID
        generation = Generations.objects.filter(unit=unitId).first()
        request.session['generationID'] = generation.generationID
        return HttpResponseRedirect('/info-third/')
    # group != null và major = null -> cần thêm major
    elif userGroup is not None and userMajor is None:
        unitId = StudentGroups.objects.get(pk=userGroup.groupID).generation.unit.unitID
        request.session['unitID'] = unitId
        return HttpResponseRedirect('/info-second/')
    # major != null và group != null
    else:
        return HttpResponseRedirect('/adminuet/profile/')

@login_required(login_url='/login/')
def second_form(request):
    """
    Form thử 2 nhập ngành và khóa sinh viên
    """
    profile = Profiles.objects.filter(user=request.user.id).first()
    userMajor = profile.major
    # major != null
    if userMajor is not None:
        return HttpResponseRedirect('/info-third/')
    # major = null
    else:
        # Có unit id trên session
        if 'unitID' in request.session:
            unitId = request.session['unitID']
            majors = ''
            generations = ''
            majors = Majors.objects.filter(unit=unitId)
            generations = Generations.objects.filter(unit=unitId)
            if request.method == 'GET':
                context = {
                    'majors': majors,
                    'generations': generations
                }
                return TemplateResponse(request, 'adminuet/secondform.html', context=context)
            else: # khi submit form
                major = request.POST.get('major')
                generation = request.POST.get('generation')

                # Validate thành công
                if validate_second_form(major, generation):
                    userId = request.user.id
                    Profiles.objects.filter(user=userId).update(major_id=major)
                    request.session['generationID'] = generation
                    del request.session['unitID']
                    return HttpResponseRedirect('/info-third/')
                else: # Validate thất bại
                    context = {
                        'majors': majors,
                        'major': major,
                        'generations': generations,
                        'generation': generation
                    }
                    messages.error(request, "Nhập thông tin chính xác.")
                    return TemplateResponse(request, 'adminuet/secondform.html', context=context)

        else:
            return HttpResponseRedirect('/info-first/')

@login_required(login_url='/login/')
def third_form(request):
    """
    Form thứ 3 nhập lớp
    """
    profile = Profiles.objects.filter(user=request.user.id).first()
    userGroup = profile.group
    # major != null
    if userGroup is not None:
        return HttpResponseRedirect('/adminuet/profile/')
    # major = null
    else:
        # Có generation id trên session
        if 'generationID' in request.session:
            generationId = request.session['generationID']
            groups = StudentGroups.objects.filter(generation=generationId)
            if request.method == 'GET':
                context = {
                    'groups': groups
                }
                return TemplateResponse(request, 'adminuet/thirdform.html', context=context)
            else:
                groups = ''
                group = request.POST.get('group')
                # Validate thành công
                if validate_third_form(group):
                    userId = request.user.id
                    Profiles.objects.filter(user=userId).update(group_id=group)
                    del request.session['generationID']
                    return HttpResponseRedirect('/adminuet/profile/')

                else: # Validate thất bại
                    context = {
                        'groups': groups,
                        'group': group
                    }
                    messages.error(request, "Nhập thông tin chính xác.")
                    return TemplateResponse(request, 'adminuet/thirdform.html', context=context)
        else:
            return HttpResponseRedirect('/info-second/')

def validate_first_form(unit, lastName, firstName, birthday):
    """
    Validate trường, tên, ngày sinh
    """
    if unit != "none" and unit != '' and lastName != '' and firstName != '' and birthday != '':
        isExistUnit = Units.objects.filter(pk=unit).exists()
        if isExistUnit:
            return True
    return False

def validate_second_form(major, generation):
    """
    Validate ngành, khóa
    """
    if major != "none" and major != "" and generation != "none" and generation != "":
        isExistMajor = Majors.objects.filter(pk=major).exists()
        isExistGeneration = Generations.objects.filter(pk=generation).exists()
        if isExistGeneration and isExistMajor:
            return True
    return False

def validate_third_form(group):
    """
    Validate lớp
    """
    if group != "none" and group != "":
        isExistGroup = StudentGroups.objects.filter(pk=group).exists()
        if isExistGroup:
            return True
    return False
