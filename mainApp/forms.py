from django import forms
from .models import Units, Years, Semesters, Courses, Majors, Generations, Functions, Roles, Profiles, StudentGroups, Major_Course, Transcript, CustomUser, DumpModel
import json

class UnitForm(forms.ModelForm):
    class Meta:
        model = Units
        fields = '__all__'
        labels = {
            'unitName': 'Tên trường',
            'unitDescription': 'Thông tin chi tiết'
        }
    def __init__(self, *args, **kwargs):
        super(UnitForm, self).__init__(*args, **kwargs)
        self.fields['unitDescription'].required = False
        self.fields['unitDescription'].initial = 'Chưa có thông tin'

class YearForm(forms.ModelForm):
    class Meta:
        model = Years
        fields = '__all__'
        labels = {
            'yearName': 'Năm học',
            'openingDay': 'Ngày khai giảng',
            'active': 'Kích hoạt'
        }
    def __init__(self, *args, **kwargs):
        super(YearForm, self).__init__(*args, **kwargs)
        # self.fields['openingDay'].required = False

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semesters
        fields = '__all__'
        labels = {
            'semesterName': 'Tên kỳ học',
            'year': 'Năm học',
            'beginDay': 'Ngày bắt đầu',
            'endDay': 'Ngày kết thúc',
        }
    def __init__(self, *args, **kwargs):
        super(SemesterForm, self).__init__(*args, **kwargs)
        list_year = Years.objects.filter(active='True')
        self.fields['year'].empty_label = 'Lựa chọn'
        self.fields['year'].queryset = list_year
        # self.fields['beginDay'].required = False 
        # self.fields['endDay'].required = False  
        self.fields['beginDay'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['endDay'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']

class CoursesForm(forms.ModelForm):
    class Meta:
        model = Courses
        fields = '__all__'
        labels = {
            'courseCode': 'Mã môn học',
            'courseName': 'Tên môn học',
            'unit': 'Trường',
            'credit': 'Số tín chỉ',
        }
    def __init__(self, *args, **kwargs):
        super(CoursesForm, self).__init__(*args, **kwargs)
        # self.fields['unit'].initial = Units.objects.filter().first()
        self.fields['unit'].empty_label = 'Lựa chọn'

class MajorsForm(forms.ModelForm):
    class Meta:
        model = Majors
        fields = '__all__'
        labels = {
            'majorName': 'Tên ngành',
            'majorDescription': 'Thông tin chi tiết',
            'unit': 'Trường',
        }
    def __init__(self, *args, **kwargs):
        super(MajorsForm, self).__init__(*args, **kwargs)
        self.fields['unit'].empty_label = 'Lựa chọn'
        self.fields['majorDescription'].required = False
        self.fields['majorDescription'].initial = 'Chưa có thông tin'

class GenerationForm(forms.ModelForm):
    class Meta:
        model = Generations
        fields = '__all__'
        labels = {
            'generationName': 'Tên Khóa',
            'beginningYear': 'Năm học bắt đầu',
            'unit': 'Trường'
        }
    def __init__(self, *args, **kwargs):
        super(GenerationForm, self).__init__(*args, **kwargs)
        self.fields['beginningYear'].empty_label = 'Lựa chọn'
        self.fields['unit'].empty_label = 'Lựa chọn'

class FunctionForm(forms.ModelForm):
    class Meta:
        model = Functions
        fields = '__all__'
        labels = {
            'functionName': 'Tên chức năng'
        }
    def __init__(self, *args, **kwargs):
        super(FunctionForm, self).__init__(*args, **kwargs)
        self.fields['functionName'].required = True

class RoleForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = '__all__'
        labels = {
            'roleName': 'Tên vai trò',
            'roleDescription': 'Mô tả'
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = StudentGroups
        fields ='__all__'
        labels = {
            'groupName': 'Lớp',
            'generation': 'Khóa'
        }
    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['generation'].empty_label = 'Lựa chọn'

class UserForm(forms.ModelForm):
    class Meta:
        model = Profiles
        fields = '__all__'
        labels = {
            'user': 'Tài khoản',
            'firstName': 'Họ',
            'lastName': 'Đệm, Tên',
            'email': 'Email',
            'MSSV': 'MSSV',
            'gender': 'Giới tính',
            'birthday': 'Ngày sinh',
            'group': 'Lớp',
            'major': 'Ngành',
        }
    
class TrainingframeworkForm(forms.ModelForm):
    class Meta:
        model = Major_Course
        fields = '__all__'
        labels = {
            'course': 'Môn học',
            'major': 'Ngành',
            'semesterRecommended': 'Kỳ học gợi ý',
        }
    def __init__(self, *args, **kwargs):
        super(TrainingframeworkForm, self).__init__(*args, **kwargs)
        self.fields['course'].empty_label = 'Lựa chọn'
        self.fields['major'].empty_label = 'Lựa chọn'

class TranscriptForm(forms.ModelForm):
    class Meta:
        model = Transcript
        fields = '__all__'
        labels = {
            'student': 'Sinh viên',
            'course': 'Môn học',
            'semester': 'Kỳ',
            'grade': 'Điểm',
        }
    def __init__(self, *args, **kwargs):
        super(TranscriptForm, self).__init__(*args, **kwargs)
        self.fields['student'].empty_label = 'Lựa chọn'
        self.fields['course'].empty_label = 'Lựa chọn'
        self.fields['semester'].empty_label = 'Lựa chọn'


class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'
        labels = {
            # 'role': 'Vai trò',
            'username': 'Tên đăng nhập',
            'password': 'Mật khẩu',
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        self.fields['role'].empty_label = 'Lựa chọn'


class DumpModelForm(forms.ModelForm):
    class Meta:
        model = DumpModel
        fields = ('dumpModelID', 'modelName', 'active')

        widgets = {
            'modelName': forms.TextInput(attrs={'hidden': True, 'disabled': True}),
            'active': forms.CheckboxInput(attrs={'hidden': True, 'disabled': True}),
        }

    def __init__(self, *args, **kwargs):
        super(DumpModelForm, self).__init__(*args, **kwargs)
        self.fields['modelName'].required = False
        self.fields['modelName'].label = False
        self.fields['active'].label = False

        order = ['modelName']  # 'dumpModelID',
        params = json.loads(self.instance.param)
        args = json.loads(self.instance.args)

        for param, value in params.items():
            type = value.get('type')
            default = value.get('default')
            current_value = args.get(param)
            options = value.get('options')

            default = default if current_value is None else current_value
            if options is None:
                if type == 'float':
                    self.fields[param] = forms.FloatField(initial=default, widget=forms.NumberInput(attrs={'step': "any"}))
                elif type == 'int':
                    self.fields[param] = forms.IntegerField(initial=default)
                else:
                    self.fields[param] = forms.CharField(max_length=50, initial=default)
            else:
                choices = ((opt, opt) for opt in options)
                self.fields[param] = forms.ChoiceField(choices=choices, initial=default)
            self.fields[param].widget.attrs.update({
                'data-toggle': "tooltip",
                'title': value.get('description'),
                'data-placement': 'right',
                'data-container': 'body',
            })
            order.append(param)

        order.append('active')
        self.order_fields(order)

    def save(self, commit=True):
        self.instance.active = True
        param = json.loads(self.instance.param)
        args = {}
        for key, value in param.items():
            args[key] = self.cleaned_data[key]
        self.instance.args = json.dumps(args)

        try:
            DumpModel.objects.filter(active=True).update(active=False)
            self.instance.save()
            return True
        except Exception as e:
            print(e)
            return False

class LoginForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')
        labels = {
            'username': 'Tên đăng nhập',
            'password': 'Mật khẩu',
        }
