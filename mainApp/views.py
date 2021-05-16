from django.shortcuts import render


from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def profile_page(request):
    return render(request, 'student/profile.html')

@login_required(login_url='/login/')
def transcript_page(request):
    return render(request, 'student/transcript.html')

@login_required(login_url='/login/')
def changepassword_page(request):
    return render(request, 'student/changepassword.html')

@login_required(login_url='/login/')
def suggestioncourse_page(request):
    return render(request, 'student/suggestioncourse.html')

@login_required(login_url='/login/')
def scoreforecast_page(request):
    return render(request, 'student/scoreforecast.html')

@login_required(login_url='/login/')
def statistical_page(request):
    return render(request, 'student/statistical.html')

