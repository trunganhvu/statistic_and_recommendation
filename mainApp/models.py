from django.db import models
import psycopg2
from psycopg2 import extras
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

TRAIN_DATA_STORAGE = FileSystemStorage(location=settings.TRAIN_DATA_ROOT)
DUMPED_MODEL_STORAGE = FileSystemStorage(location=settings.DUMPED_MODEL_ROOT)


def get_current_semester():
    today = timezone.now().date()

    semesters = Semesters.objects.filter(beginDay__lte=today).order_by('-beginDay')

    if len(semesters) <= 0:
        semesters = Semesters.objects.filter(endDay__gte=today).order_by('endDay')

    if len(semesters) <= 0:
        current_semester = Semesters.objects.last()
    else:
        current_semester = semesters[0]

    return current_semester


def execute_values(conn, df, table):
    """
    Using psycopg2.extras.execute_values() to insert the dataframe
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = '"' + '","'.join(list(df.columns)) + '"'
    # SQL quert to execute
    query = 'INSERT INTO public."%s"(%s) VALUES %%s' % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("execute_values() done")
    cursor.close()


def model_field_exists(model, field):
    try:
        model._meta.get_field(field)
        return True
    except Exception as e:
        # print(e)
        return False


def create_from_DF(df, model: models.Model, searching_cols: list):
    # for col in df.columns:
    #     if ~model_field_exists(model, col):
    #         print("col: {}".format(col))
    #         df.drop(col, axis=1, inplace=True)
    #         print(df)
    # data for searching the data row
    search = dict.fromkeys(searching_cols)
    # other data use when create
    defaults = dict.fromkeys(list(set(df.columns) - set(searching_cols)))
    # Create a list of tupples from the dataframe values
    object_list = []
    for i, row in df.iterrows():
        for k in search.keys():
            search[k] = row[k]

        for k in defaults.keys():
            defaults[k] = row[k]
        obj, created = model.objects.get_or_create(**search, defaults=defaults)
        object_list.append(obj)
    return object_list


def update_from_DF(df, model: models.Model, searching_cols: list):
    # for col in df.columns:
    #     if ~model_field_exists(model, col):
    #         print("{} is not one of {} field".format(col, model.__name__))
    #         return 1
    # data for searching the data row
    search = dict.fromkeys(searching_cols)
    # other data use when create
    defaults = dict.fromkeys(list(set(df.columns) - set(searching_cols)))

    # Create a list of tupples from the dataframe values
    object_list = []
    for v in df.iterrows():
        for k in search.keys():
            search[k] = v[k]

        for k in defaults.keys():
            defaults[k] = v[k]
        obj, created = model.objects.update_or_create(**search, defaults=defaults)
        object_list.append(obj)
    return object_list


def semester_rank(current_semester_id=None, profile_id: int = None, group_id: int = None, generation_id: int = None,
                  year_id: int = None, semester_id: int = None):
    """
    Cho biết thứ tự của kỳ học hiện tại đối với một lớp, khóa, hay kỳ nào đó (gọi chung là đối tượng) dựa theo id của chúng.
    Những kỳ học tính từ kỳ đầu tiên của đối tượng được chọn có kết thúc trước beginday của kỳ học hiện tại sẽ được đếm.
    :param current_semester_id:
    :param profile_id:
    :param group_id:
    :param generation_id:
    :param year_id:
    :param semester_id:
    :return:
    """
    try:
        if current_semester_id is None:
            current_semester = get_current_semester()
        else:
            current_semester = Semesters.objects.get(pk=current_semester_id)

        if profile_id is not None and profile_id > 0:
            group_id = Profiles.objects.get(pk=profile_id).group_id

        if group_id is not None and group_id > 0:
            generation_id = StudentGroups.objects.get(pk=group_id).generation_id

        if generation_id is not None and generation_id > 0:
            year_id = Generations.objects.get(pk=generation_id).beginningYear_id

        if year_id is not None and year_id > 0:
            semester = Semesters.objects.filter(year_id=year_id).first()
        else:
            semester = Semesters.objects.get(pk=semester_id)

        if current_semester.pk == semester.pk:
            return 0

        sem_begin = semester.beginDay
        cur_sem_begin = current_semester.beginDay

        semester_rank = len(Semesters.objects.filter(endDay__gt=sem_begin, endDay__lt=cur_sem_begin))
        if semester_rank <= 0:
            semester_rank = -len(Semesters.objects.filter(endDay__gt=cur_sem_begin, endDay__lt=sem_begin))

        return semester_rank

    except Exception as e:
        print(e)
        return None


def transcript_path_and_rename(instance: models.Model, filename: str):
    folder_name = 'transcript/'
    filename = filename.replace('/', '_').replace('\\', '_')
    # get filename
    if instance.pk:
        filename = '{}_{}'.format(instance.pk, filename)
    else:
        # set filename as random string
        filename = '{}_{}'.format(uuid4().hex, filename)
    # return the whole path to the file
    return folder_name + filename


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

"""
Tên table trong DB: mainApp_years
"""
class Years(models.Model):
    yearID = models.AutoField(primary_key=True)
    yearName = models.CharField(max_length=50)
    openingDay = models.DateField(null=False)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.yearName

    def save(self, *args, **kwargs):
        other_years = Years.objects.filter(openingDay__year=self.openingDay.year)
        if len(other_years) > 1 or (len(other_years) == 1 and other_years[0].pk != self.pk):
            raise Exception("This year already have opening day")

        super(Years, self).save(*args, **kwargs)

"""
Tên table trong DB: mainApp_semesters
"""
class Semesters(models.Model):
    semesterID = models.AutoField(primary_key=True)
    semesterName = models.CharField(max_length=50)
    year = models.ForeignKey(Years, on_delete=models.CASCADE)
    beginDay = models.DateField(null=False)
    endDay = models.DateField(null=False)

    def __str__(self):
        return self.semesterName

"""
Tên table trong DB: mainApp_units
"""
class Units(models.Model):
    unitID = models.AutoField(primary_key=True)
    unitName = models.CharField(max_length=100) #unique=True
    unitDescription = models.CharField(max_length=500, default="", null=True)

    def __str__(self):
        return self.unitName

"""
Tên table trong DB: mainApp_generations
"""
class Generations(models.Model):
    generationID = models.AutoField(primary_key=True)
    generationName = models.CharField(max_length=10)
    beginningYear = models.ForeignKey(Years, on_delete=models.CASCADE)
    unit = models.ForeignKey(Units, on_delete=models.CASCADE)

    def __str__(self):
        return self.generationName + ' - ' + self.unit.unitName

"""
Tên table trong DB: mainApp_studentgroups
"""
class StudentGroups(models.Model):
    groupID = models.AutoField(primary_key=True)
    groupName = models.CharField(max_length=25)
    generation = models.ForeignKey(Generations, on_delete=models.CASCADE)

    def __str__(self):
        return self.groupName + ' - ' + self.generation.unit

"""
Tên table trong DB: mainApp_majors
"""
class Majors(models.Model):
    majorID = models.AutoField(primary_key=True)
    majorName = models.CharField(max_length=100)
    majorDescription = models.CharField(max_length=255, default="", null=True)
    unit = models.ForeignKey(Units, on_delete=models.CASCADE)

    def __str__(self):
        return self.majorName

"""
Tên table trong DB: mainApp_courses
"""
class Courses(models.Model):
    courseID = models.AutoField(primary_key=True)
    unit = models.ForeignKey(Units, on_delete=models.CASCADE)
    courseCode = models.CharField(max_length=20, unique=True)
    courseName = models.CharField(max_length=100)
    credit = models.IntegerField(default=0)

    def __str__(self):
        return self.courseCode + ' - ' + self.courseName

"""
Tên table trong DB: mainApp_major_course
"""
class Major_Course(models.Model):
    """
    Một mnô học (course) trong mỗi chuyên ngành (major) có thể được đề xuất học trong nhiều kỳ khác nhau (semesterRecommended)
    """
    ID = models.AutoField(primary_key=True)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    major = models.ForeignKey(Majors, on_delete=models.CASCADE)
    semesterRecommended = models.IntegerField(default=0)

"""
Tên table trong DB: mainApp_functions
"""
class Functions(models.Model):
    """
    Danh sách các chức năng hệ thống để dùng trong việc phân quyền
    """
    functionID = models.AutoField(primary_key=True)
    functionName = models.CharField(max_length=50)

    def __str__(self):
        return self.functionName

"""
Tên table trong DB: mainApp_roles
"""
class Roles(models.Model):
    """
    Danh sách các vai trò trong hệ thống để phân quyền theo vai trò
    """
    roleID = models.AutoField(primary_key=True)
    roleName = models.CharField(max_length=50)
    roleDescription = models.CharField(max_length=255, default="", null=True)

    def __str__(self):
        return self.roleName

"""
Tên table trong DB: mainApp_role_function
"""
class Role_Function(models.Model):
    """
    Danh sách các chức năng được phân cho các vai trò khác nhau
    """
    ID = models.AutoField(primary_key=True)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    function = models.ForeignKey(Functions, on_delete=models.CASCADE)
    # role = models.IntegerField(blank=False)
    # function = models.IntegerField(blank=False)

"""
Tên table trong DB: mainApp_customuser
"""
class CustomUser(AbstractUser):
    # id | password | last_login | username | date_joined | role_id
    is_superuser = None
    first_name = None
    last_name = None
    email = None
    is_staff = None
    # is_active = None
    groups = None
    user_permissions = None

    role = models.ForeignKey(Roles, null=True, on_delete=models.SET_NULL)
    unit_role = models.IntegerField(default=None, null=True)

    objects = CustomUserManager()

    dictFunctionName = {
        "Thống kê GPA sinh viên": "statistical-gpa-student",
        "Thống kê GPA khóa": "statistical-gpa",
        "Thống kê điểm trung bình": "course-avg",
        "Thống kê phổ điểm môn học": "statistical",
        "Gợi ý môn học": "suggestioncourse",
        "Dự báo kết quả học tập": "scoreforecast",
        "Quản lý vai trò": "role",
        "Quản lý chức năng": "function",
        "Quản lý lớp": "group",
        "Quản lý khung đào tạo": "trainingframework",
        "Quản lý môn học": "course",
        "Quản lý khóa": "generation",
        "Quản lý kỳ học": "semester",
        "Quản lý năm học": "year",
        "Quản lý trường": "unit",
        "Quản lý ngành": "major",
        "Quản trị logs": "logs",
        "Chọn mô hình": "configmodel",
        "Quản trị kết quả học tập": "learningoutcome",
        "Quản trị người dùng": "user",
        "Tính toán thống kê GPA": "calculategpa",
        "Xem kết quả học tập": "viewlearningoutcome",
        "Chọn dữ liệu": "choicedata",
        "Dự báo khóa": "scoreforecastgeneration"
    }

    def list_function(self):
        if self.pk is None:
            return []

        functions = set(CustomUser_Function.objects.filter(user=self).values_list("function__functionName", flat=True))
        if self.role_id is not None:
            functions.update(Role_Function.objects.filter(role=self.role_id).values_list("function__functionName", flat=True))

        function_list = [self.dictFunctionName[funct] for funct in functions]
        return function_list

    def __str__(self):
        return self.username

"""
Tên table trong DB: mainApp_customUser_function
"""
class CustomUser_Function(models.Model):
    """
    Danh sách lưu user có thêm những function khác ngoài Role đã có của User
    """
    ID = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    function = models.ForeignKey(Functions, on_delete=models.CASCADE)

"""
Tên table trong DB: mainApp_profiles
"""
class Profiles(models.Model):
    profileID = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=254, null=True)
    MSSV = models.CharField(max_length=10, null=True)
    gender = models.CharField(max_length=10, choices=[
        ('Nam', 'Nam'),
        ('Nữ', 'Nữ'),
    ], default='Nam')
    birthday = models.DateField()
    group = models.ForeignKey(StudentGroups, on_delete=models.CASCADE, null=True)
    major = models.ForeignKey(Majors, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.MSSV

"""
Tên table trong DB: mainApp_transcriptfiles
"""
class TranscriptFiles(models.Model):
    """
    là bảng lưu đường dẫn tới file bảng điểm các kỳ của từng lớp
    """
    fileID = models.AutoField(primary_key=True)
    group = models.ForeignKey(StudentGroups, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semesters, on_delete=models.CASCADE)
    major = models.ForeignKey(Majors, on_delete=models.SET_NULL, null=True)
    transcript = models.FileField(upload_to=transcript_path_and_rename)
    extracted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.transcript.name.split('/')[-1])

"""
Tên table trong DB: mainApp_transcript
"""
class Transcript(models.Model):
    """
    Lưu lịch sử bảng điểm của người dùng với id use, stt bẳng điểm và các điểm (student ánh xạ tới profileID).
    """
    transcriptID = models.AutoField(primary_key=True)
    student = models.ForeignKey(Profiles, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semesters, on_delete=models.CASCADE)
    grade = models.FloatField()

    def __str__(self):
        return self.grade

"""
Tên table trong DB: mainApp_traindata
"""
class TrainData(models.Model):
    trainDataID = models.AutoField(primary_key=True)
    dataPath = models.FileField(storage=TRAIN_DATA_STORAGE)
    major = models.ForeignKey(Majors, on_delete=models.DO_NOTHING, null=True)
    updateTime = models.DateTimeField('date_published', auto_now=True)

    def __str__(self):
        return str(self.major_id) + ": " + self.dataPath.name

"""
Tên table trong DB: mainApp_predicthistory
"""
class PredictHistory(models.Model):
    PredictHistoryID = models.AutoField(primary_key=True)
    student = models.ForeignKey(Profiles, on_delete=models.DO_NOTHING)
    course = models.ForeignKey(Courses, on_delete=models.DO_NOTHING)
    grade = models.FloatField()
    semester = models.ForeignKey(Semesters, on_delete=models.DO_NOTHING)
    predictTime = models.DateTimeField(auto_now_add=True)

"""
Tên table trong DB: mainApp_gradepredicted
"""
class GradePredicted(models.Model):
    """
    Lưu lịch sử dự đoán điểm với id bảng điểm người dùng nếu thời điểm trong lần dự đoán cuối sớm hơn scoreUpdateTime
    thì sẽ thực hiện dự đoán lại.
    """
    predictID = models.AutoField(primary_key=True)
    student = models.ForeignKey(Profiles, on_delete=models.CASCADE)
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    grade = models.FloatField()
    predictTime = models.DateTimeField(auto_now_add=True)

"""
Tên table trong DB: mainApp_gpa
"""
class GPA(models.Model):
    """
    Lưu điểm gpa của sinh viên
    """
    gpaID = models.AutoField(primary_key=True)
    student = models.ForeignKey(Profiles, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semesters, on_delete=models.DO_NOTHING)
    semesterRank = models.IntegerField(null=True)
    semesterGpa = models.FloatField()
    currentGpa = models.FloatField()

"""
Tên table trong DB: mainApp_dumpmodel
"""
class DumpModel(models.Model):
    dumpModelID = models.AutoField(primary_key=True)
    dumpFile = models.FileField(unique=True, storage=DUMPED_MODEL_STORAGE)
    modelName = models.CharField(max_length=254, null=True)
    param = models.CharField(max_length=1000, null=True)
    updateTime = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=False)
    args = models.CharField(max_length=254, null=True)

    def __str__(self):
        return self.modelName

"""
Tên table trong DB: mainApp_logs
"""
class Logs(models.Model):
    """
    Ghi nhật ký sử dụng log tất cả các tài khoản tương tác với hệ thống
    """
    logID = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING)
    action = models.CharField(max_length=50)
    content = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)

class TimeLinePredicted(models.Model):
    """
    Lưu lại thời gian các lần tính toán dự báo điểm theo khóa
    """
    timeLineID = models.AutoField(primary_key=True)
    major = models.ForeignKey(Majors, on_delete=models.CASCADE)
    generation = generation = models.ForeignKey(Generations, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)