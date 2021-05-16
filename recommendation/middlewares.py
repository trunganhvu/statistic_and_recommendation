from django.http import HttpResponseRedirect
from mainApp.middlewares import FunctionMiddleware


class AdminOnlyMiddleware(FunctionMiddleware):
    def __call__(self, request):
        response = self.get_response(request)
        return response

    def post_valid_unit(self, request):
        post_args = request.POST
        return self.valid_unit(post_args.get('unit_id'),
                               post_args.get('generation_id'),
                               post_args.get('major_id'),
                               post_args.get('group_id'),
                               post_args.get('student_id'),
                               post_args.get('course_id'))


    def process_view(self, request, view_func, view_args, view_kwargs):
        unit_role = request.user.unit_role
        if unit_role is None:
            return HttpResponseRedirect('/')
        elif unit_role == 0:
            return view_func(request, *view_args, **view_kwargs)
        else:
            if request.method == 'POST':
                post_unit = self.post_valid_unit(request)
                if post_unit == 'all':
                    return HttpResponseRedirect('/')
                elif post_unit is not None and post_unit.pk != unit_role:
                    return HttpResponseRedirect('/')

            return view_func(request, *view_args, **view_kwargs)

    def process_template_response(self, request, response):
        return response


class AdminPostOnlyMiddleware(AdminOnlyMiddleware):
    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method == 'POST':
            return super(AdminPostOnlyMiddleware, self).process_view(request, view_func, view_args, view_kwargs)
        else:
            return view_func(request, *view_args, **view_kwargs)
