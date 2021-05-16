from mainApp.models import Logs
from mainApp.serializers.logserializer import LogSerializer
import math
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
import socket
from datetime import datetime
import pytz
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

def getCurrentTime():
    """
    Lấy thời gian hiện tại ở VN
    """
    return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')

def getIpAddress():
    """
    Lấy IP của máy client
    """
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

def createLog(request, action, result):
    """
    Thực hiện tạo lịch sử  log
    """
    ip_address = getIpAddress()
    time = getCurrentTime()
    currentUser = request.user
    record_logs(currentUser.id, ip_address, time, action, result)

def record_logs(user, ip, time, action, content):
    """
    Thực hiện ghi log
    """
    log = Logs.objects.create(user_id=user, action=action, content=content, time=time)
    log.save()

@login_required(login_url='/login/')
def logPagination_page(request, num=1, limit=10):
    """
    Hiện thị trang ghi log có trang và giới hạn bản ghi (chưa có dữ liệu)
    """
    if checkInUrl(request, 'logs') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    return TemplateResponse(request, 'adminuet/log.html', {'page': num, 'limit': limit})

@login_required(login_url='/login/')
@api_view(['GET'])
def log_page(request, offset, limit):
    """
    Lấy danh sách các log từ vị trí offset và limit bản ghi
    """
    if checkInUrl(request, 'logs') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'GET':
        logs = Logs.objects.order_by('-logID').all()
        logList = logs[offset:offset + limit].select_related('user')
        logCount = logs.count()
        logSerializer = LogSerializer(logList, many=True)
        for log, logS in zip(logList, logSerializer.data):
            logS['user'] = log.user.username
            timeInDB = log.time
            tz = pytz.timezone('Asia/Ho_Chi_Minh')
            timeInDB = timeInDB.replace(tzinfo=pytz.UTC)
            resultTime = timeInDB.astimezone(tz)
            logS['time'] = resultTime.strftime('%Y-%m-%d %H:%M:%S')
        page = math.ceil(logCount/limit)
        data = {
            'data': logSerializer.data,
            'numberOfPage': page,
        }
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        time = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
        currentUser = request.user
        record_logs(currentUser.id, ip_address, time, 'VIEW', 'Log page')
        return Response(data)

@login_required(login_url='/login/')
def delete_log(request):
    """
    Xóa log từ vị trong khoảng thời gian
    """
    if checkInUrl(request, 'logs') is False:
        listFunction = request.user.list_function()
        return HttpResponseRedirect(reverse(listFunction[0]))
    if request.method == 'POST':
        fromeDate = request.POST['fromdate']
        toDate = request.POST['todate']
        list_log = Logs.objects.filter(time__range=(fromeDate, toDate))
        try:
            list_log.delete()
            messages.success(request, "Xóa thành công.")
        except (Exception) as error:
            print(error)
            messages.error(request, "Thao tác thất bại.")
    return redirect('/adminuet/logs/')