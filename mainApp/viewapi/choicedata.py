from django.views.decorators.http import require_http_methods
from django.template.response import TemplateResponse
from mainApp.middlewares import checkInUrl
from django.urls import reverse
from django.http import HttpResponseRedirect
from mainApp.viewapi.logs import createLog
from django.contrib import messages
from mainApp.models import Generations,TrainData
from django.contrib.auth.decorators import login_required
from recommendation import views

@login_required(login_url='/login/')
def get_choice_data(request):
    """
    Lấy danh sách các tập dữ liệu huấn luyện
    """
    try:
        if checkInUrl(request, 'choicedata') is False:
            listFunction = request.user.list_function()
            return HttpResponseRedirect(reverse(listFunction[0]))
        unitRole = request.user.unit_role
        # Rule admin
        if unitRole == 0:
            generations = Generations.objects.order_by('-generationName').all()
            trainDatas = TrainData.objects.all()
        else: # Quản trị cấp trường
            generations = Generations.objects.order_by('-generationName').filter(unit_id=unitRole).all()
            trainDatas = TrainData.objects.filter(major__unit_id=unitRole)
        context = {
            "generations": generations,
            "trainDatas": trainDatas
        }
        if request.method == 'POST':
            major = request.POST['major_id']
            generations = request.POST.getlist('generation_id')
            if len(generations) == 0:
                context['major'] = major
                raise Exception("Error")
            if major is None:
                context['generationLast'] = generations
                raise Exception("Error")
            # uri = request.build_absolute_uri('/')[:-1] + "/recommend/model_data"
            result = views.create_train_data_file1(int(major), generations)['successed']

            if not result:
                messages.error(request,'Thao tác thất bại')
                context['generationLast'] = generations
                context['major'] = major
            else:
                messages.success(request, "Thao tác thành công")
    except Exception as error:
        print("false")

        messages.error(request, "Thao tác thất bại.")
    return TemplateResponse(request, 'adminuet/choicedata.html', context=context)

def post_choice_data(request):
    """
    Thực hiện chọn tập dữ liệu huấn luyện
    """
    return TemplateResponse(request, 'adminuet/choicedata.html')
