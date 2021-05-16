from mainApp.models import Profiles, CustomUser, StudentGroups, Majors, Units, Generations, Courses, Major_Course
from django.urls import get_resolver
from django.http import HttpResponseRedirect

def checkInUrl(request, idName):
    """ Kiểm tra quyền truy cập chức năng của người dùng.
    Kiểm tra xem chức năng cần truy cập có nằm trong danh sách chức năng của người dùng không và trả về True hoặc False
    
    :param request: 
    :param idName: 
    :return: 
    """
    if request.user.is_authenticated:
        listFuntion = request.user.list_function()
        return idName in listFuntion
    return False

class FunctionMiddleware:
    """ Một middleware chung cho tất cả các request đến hệ thống kiểm tra sơ bộ các request. Sẽ cho phép hoặc điều hướng nếu cần thiết
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def valid_unit(self, unit_id=None, generation_id=None, major_id=None, group_id=None, profile_id=None, course_id=None):
        """ Kiểm tra đơn vị (unit) sở hữu các thông tin yêu cầu (về unit, generation, ...)
        - Nếu các thông tin yêu cầu thuộc cùng một đơn vị thì trả về id của đơn vị đó
        - Nếu các thông tin yêu cầu thuộc cùng nhiều đơn vị khác nhau thì sẽ trả về 0
        - Nếu đầu vào đều là None thì sẽ trả về None 
        :param unit_id:
        :param generation_id:
        :param major_id:
        :param group_id:
        :param profile_id:
        :param course_id:
        :return:
        """
        if unit_id is None and generation_id is None and major_id is None and group_id is None and profile_id is None and course_id is None:
            return None

        try:
            student = None if profile_id in [None, 0] else Profiles.objects.get(pk=profile_id)

            course = None if course_id in [None, 0] else Courses.objects.get(pk=course_id)

            major = None if major_id in [None, 0] else Majors.objects.get(pk=major_id)
            if student is not None and student.major is not None:
                if major is None:
                    major = student.major
                elif major != student.major:
                    raise Exception("student and major don't match.")

            group = None if group_id in [None, 0] else StudentGroups.objects.get(pk=group_id)
            if student is not None and student.group is not None:
                if group is None:
                    group = student.group
                elif group != student.group:
                    raise Exception("student and group don't match.")

            generation = None if generation_id in [None, 0] else Generations.objects.get(pk=generation_id)
            if group is not None:
                if generation is None:
                    generation = group.generation
                elif generation != group.generation:
                    raise Exception("group and generation don't match.")

            unit = None if unit_id  in [None, 0] else Units.objects.get(pk=unit_id)

            if generation is not None:
                if unit is None:
                    unit = generation.unit
                elif unit != generation.unit:
                    raise Exception("unit and generation don't match.")

            if major is not None:
                if unit is None:
                    unit = major.unit
                elif unit != major.unit:
                    raise Exception("major and unit don't match.")

            if course is not None:
                major_course = Major_Course.objects.filter(course=course)
                if major is not None and major.pk not in major_course.values_list("major_id", flat=True):
                    raise Exception("course and major don't match.")

                if unit is None:
                    unit = course.unit
                elif unit != course.unit:
                    raise Exception("course and unit don't match.")

            return 0 if unit is None else unit
        except Exception as e:
            print("FunctionMiddleware.valid_unit: ", e)

        return None

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """ Kiểm tra authenticated
        kiểm tra các thông tin yêu cầu có đúng hay không và người dùng có quyền truy cập chúng hay không
        :param request:
        :param view_func:
        :param view_args:
        :param view_kwargs:
        :return:
        """
        if request.user.is_authenticated:
            if len(set({"unit_id", "generation_id", "major_id", "group_id", "profile_id", "course_id"}).intersection(view_kwargs.keys())) > 0:  # check is url have one of those values
                try:
                    unit_role = request.user.unit_role
                    if unit_role == 0:
                        return view_func(request, *view_args, **view_kwargs)

                    else:
                        unit = self.valid_unit(view_kwargs.get("unit_id"),
                                               view_kwargs.get("generation_id"),
                                               view_kwargs.get("major_id"),
                                               view_kwargs.get("group_id"),
                                               view_kwargs.get("profile_id"),
                                               view_kwargs.get("course_id"))
                        if unit == 0:
                            raise Exception("admin role only, user must have unit_role is 0")
                        elif unit == None:
                            raise Exception('param valid')
                        else:
                            unit_id = unit.pk

                        if unit_role is None:
                            student = Profiles.objects.get(user=request.user)
                            if view_kwargs.get('profile_id') is not None and student.pk != view_kwargs.get('profile_id'):
                                    raise Exception("profile_id and user don't match")

                            if student.major.unit_id != unit_id:
                                raise Exception("student don't belong to this unit")
                            else:
                                return view_func(request, *view_args, **view_kwargs)
                        elif unit_id == unit_role:
                                return view_func(request, *view_args, **view_kwargs)

                except Exception as e:
                    print(e)

                return HttpResponseRedirect('/')
            else:
                return view_func(request, *view_args, **view_kwargs)
        else:
            s = request.path.split("/")[1]
            if s not in ['', 'login', 'static']:
                return HttpResponseRedirect('/')
            else:
                return view_func(request, *view_args, **view_kwargs)


    def process_template_response(self, request, response):
        """ xử lý trước khi chuyển các thông tin đến template và tạo trang trang web
        cung cấp thêm thông tin về các chức năng có thể truy cập của người dùng
        :param request:
        :param response:
        :return:
        """
        if request.user.is_authenticated:
            if response.context_data is None:
                response.context_data = {}

            response.context_data['dict_function'] = request.user.list_function()
        return response