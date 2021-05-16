from django.http import HttpResponseRedirect


class GPAMiddleware:
    def __init__(self, get_response):
        print("init")
        self.get_response = get_response

    def __call__(self, request):
        print('call')
        response = self.get_response(request)
        print("call oke")
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        method = view_kwargs.get('method')
        if method in ['update', 'reevaluation']:
            if request.user.unit_role is None:
                return HttpResponseRedirect('/statistic/gpa/{}/{}/{}/get'.format(view_kwargs.get('unit_id'),
                                                                                 view_kwargs.get('major_id'),
                                                                                 view_kwargs.get('generation_id')))
        elif method != 'get':
            return HttpResponseRedirect('/statistic/gpa/{}/{}/{}/get'.format(view_kwargs.get('unit_id'),
                                                                             view_kwargs.get('major_id'),
                                                                             view_kwargs.get('generation_id')))
        else:
            return view_func(request, *view_args, **view_kwargs)
