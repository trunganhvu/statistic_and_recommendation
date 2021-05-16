# recommendation views
from django.shortcuts import resolve_url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from mainApp import models as mainModel
from django.db.models import Avg, Min, Q, Count
import numpy as np
import pandas as pd
import json
from django.core import serializers
from recommendation.core.lib import calculate, process
import pickle

from django.utils.decorators import decorator_from_middleware
from .middlewares import AdminOnlyMiddleware, AdminPostOnlyMiddleware

# prepare model
MODEL = None
MAJOR_ID = None

def create_train_data_file1(major_id, generation_id):
    list_generation_id = list(map(int, generation_id))
    students = mainModel.Profiles.objects
    if list_generation_id is not None and len(list_generation_id) > 0:
        # students = students.filter(group__generation__generationID__in=list_generation_id)
        students = students.filter(group__generation_id__in=list_generation_id)

    if major_id is not None and major_id > 0:
        students = students.filter(major_id=major_id)
    students = students.all()  # tránh trường hơp list_generation_id là None và major_id <=0

    # student_id_list = students.values_list('pk', flat=True)

    score_list = mainModel.Transcript.objects.filter(student__in=students).values_list('student', 'course_id', 'grade')

    course_list = list(set([sco[1] for sco in score_list]))
    transcript = pd.DataFrame(index=students.values_list('pk', flat=True), columns=course_list, dtype=float)
    del course_list

    for student_id, course, grade in score_list:
        transcript.loc[student_id, course] = grade

    # loại bỏ bớt các sinh viên đã học ít môn, chỉ sinh viên học và qua 20 môn mới được chọn
    transcript[(transcript > 0).sum(axis=1) > 20].index


    file_name = "major_" + str(major_id) + "_train_data.csv"
    try:
        train_file = mainModel.TrainData.objects.get(major_id=major_id)
        train_file.dataPath.delete()
        train_file.dataPath.name = file_name
        train_file.save()
        created = False
    except Exception as e:
        train_file, created = mainModel.TrainData.objects.create(major_id=major_id, dataPath=file_name)
        created = True
    file = train_file.dataPath.open('w')
    transcript.to_csv(file, index=False)
    file.close()
    result = {
        'successed': True,
        'created': created,
        'train data': json.loads(serializers.serialize("json", [train_file])),
    }
    return result

@api_view(['GET', 'POST'])
@decorator_from_middleware(AdminOnlyMiddleware)
def create_train_data_file(request, major_id=None):
    """
    GET: Liệt kê các file train data đã có
    GET url: /model_data/

    POST: Gửi yêu cầu tạo (hoặc cập nhập) file train data của một ngành học
    POST url: /model_data/<int:major_id>/
    Media type: application/x-www-form-urlencoded
    POST body:
        generation_id: lặp lại, ứng với khóa học sẽ được sử dụng dữ liệu điểm làm dữ liệu huấn luyện
        e.g: generation_id=2;generation_id=3;

    :param request:
    :param major_id:
    :return:
    """
    if major_id is not None and request.method == 'POST':
        list_generation_id = list(map(int, request.POST.getlist('generation_id')))
        students = mainModel.Profiles.objects
        if list_generation_id is not None and len(list_generation_id) > 0:
            # students = students.filter(group__generation__generationID__in=list_generation_id)
            students = students.filter(group__generation_id__in=list_generation_id)

        if major_id is not None and major_id > 0:
            students = students.filter(major_id=major_id)
        students = students.all()  # tránh trường hơp list_generation_id là None và major_id <=0

        # student_id_list = students.values_list('pk', flat=True)

        score_list = mainModel.Transcript.objects.filter(student__in=students).values_list('student', 'course_id', 'grade')

        course_list = list(set([sco[1] for sco in score_list]))
        transcript = pd.DataFrame(index=students.values_list('pk', flat=True), columns=course_list, dtype=float)
        del course_list

        for student_id, course, grade in score_list:
            transcript.loc[student_id, course] = grade

        # loại bỏ bớt các sinh viên đã học ít môn, chỉ sinh viên học và qua 20 môn mới được chọn
        transcript[(transcript > 0).sum(axis=1) > 20].index


        file_name = "major_" + str(major_id) + "_train_data.csv"
        try:
            train_file = mainModel.TrainData.objects.get(major_id=major_id)
            train_file.dataPath.delete()
            train_file.dataPath.name = file_name
            train_file.save()
            created = False
        except Exception as e:
            train_file, created = mainModel.TrainData.objects.create(major_id=major_id, dataPath=file_name)
            created = True
        file = train_file.dataPath.open('w')
        transcript.to_csv(file, index=False)
        file.close()
        result = {
            'created': created,
            'train data': json.loads(serializers.serialize("json", [train_file])),
        }
        return result
    else:
        result = dict()
        train_file = mainModel.TrainData.objects
        if major_id is not None:
            train_file = train_file.filter(major_id=major_id)
        else:
            train_file = train_file.all().order_by("major_id")
        print(train_file.values("major", "dataPath", "updateTime"))
        # print(train_file.values_list("major", "dataPath", "updateTime"))
        # result['train data'] = json.loads(serializers.serialize("json", train_file))
        result = dict({'train data': []})
        for major_id, dataPath, updateTime in train_file.values_list("major", "dataPath", "updateTime"):
            result['train data'].append({
                'major_id': major_id,
                'file_name': dataPath,
                'update_time': updateTime
            })
        return Response(result)
        # return Response({"oke":"oke"})


def train_data_to_DF(major_id):
    """Trả về dữ liệu huấn luyện tùy theo từng ngành dưới dạng DataFrame

    :param major_id:
    :return:
    """
    try:
        data_file = mainModel.TrainData.objects.get(major_id=major_id).dataPath.open('r')
        train_data = pd.read_csv(data_file)
        train_data.columns = map(int, train_data.columns)
        data_file.close()
        return train_data
    except mainModel.TrainData.DoesNotExist as e:
        print("This major haven't train data yet")
        return None


def student_grade_to_DF(student_id):
    """
    Sử dụng điểm của sinh viên từ cơ sở dữ liệu chuyển đổi dữ liệu thành dạng bảng bảng DataFrame phù hợp làm đầu vào cho các mô hình dự đoán
    :param student_id:
    :return:
    """
    student_grade = mainModel.Transcript.objects.filter(student_id=student_id)
    # cols = [g[0] for g in student_grade.values_list('course_id')]
    transcript = pd.DataFrame(index=[student_id])
    for course_id, grade in student_grade.values_list('course_id', 'grade'):
        transcript[course_id] = grade

    return transcript


def init_model():
    """
    Khởi tạo model dự đoán môn học theo mặc định
    :return:
    """
    global MODEL
    try:
        dump_model = mainModel.DumpModel.objects.get(active=True)
        MODEL = pickle.load(dump_model.dumpFile.open())
        MODEL.__init__(**json.loads(dump_model.args))
    except Exception as e:
        print(e)
        print('Please check model config in /config_model')
    return MODEL


def fit_model(major_id):
    """ Huấn luyện mô hình
    :param major_id:
    :return:
    """
    global MODEL
    global MAJOR_ID
    MAJOR_ID = major_id
    train_data = train_data_to_DF(major_id)
    if train_data is None:
        raise Exception("fit_model error: train_data is empty or faulty")

    if MODEL is None:
        init_model()
    MODEL.fit(train_data)
    return MODEL


def predict_grade(student, semester=None, course_id_list: list = None, fitting: bool = True, save_history: bool = True):
    """ dự đoán điểm cho sinh viên
    :param student: Profile Model, một đối tượng Profile
    :param semester: Semester Model, một đối tượng Semester
    :param course_id_list: a list or a query set of Courses Model, một danh sách đối tượng Courses
    :param fitting: bool type, decide to fit MODEL with new major train data or not,
    biến quyết định xem có đổi train data của MODEL hay giữ nguyên train data của lần dự trước.
    Cần fitting lại khi thay đổi chuyên ngành so với lần dự đoán trước
    :param save_history: bool type, decide to save the predict result to PredictHistory table or not,
    biến quyết định xem có lưu lại kết quả dự đoán vào PredictHistory hay không
    :return:
    """
    global MODEL
    global MAJOR_ID

    # checking and fit MODEL
    if fitting or MAJOR_ID is None or MAJOR_ID != student.major_id:
        try:
            fit_model(major_id=student.major_id)
        except Exception as e:
            Response({"error": e})

    # kiểm tra course_id_list
    if course_id_list is None or len(course_id_list) < 1:
        if semester is None:
            semester = mainModel.get_current_semester()
        semester_rank = mainModel.semester_rank(group_id=student.group_id, current_semester_id=semester.pk)
        course_id_list = mainModel.Major_Course.objects.filter(major_id=student.major_id, semesterRecommended=semester_rank + 1
                                                               ).values_list('course_id', flat=True)
        del semester_rank
    student_grade = student_grade_to_DF(student_id=student.pk)
    course_id_list = list(set(course_id_list) - set(student_grade.columns))
    if len(course_id_list) < 1:
        return []

    # Dự đoán điểm
    predict_df = MODEL.predict(student_grade, course_id_list)
    predict_df = predict_df.iloc[0, :].dropna()

    # lưu điểm dự đoán vào DB
    grade_predicted_list = []
    for course_id, grade in predict_df.items():
        grade_predicted, created = mainModel.GradePredicted.objects.update_or_create(student=student, course_id=course_id,
                                                                                     defaults={'grade': round(grade, 2)})
        grade_predicted_list.append(grade_predicted)

    if save_history:
        if semester is None:
            semester = mainModel.get_current_semester()
        for course_id, grade in predict_df.items():
            mainModel.PredictHistory.objects.create(student=student, course_id=course_id, grade=round(grade, 2), semester=semester)

    return grade_predicted_list


@api_view(['GET', 'POST'])
# @decorator_from_middleware(AdminPostOnlyMiddleware)
def predict_grade_student(request, profile_id):
    """url: /predict_grade/s_<int:profile_id>/
    GET: Trả về điểm số dự đoán cho một số môn học đã dự đoán trước đó
    POST: Gửi yêu cầu dự đoán điểm các môn học, trả về điểm số dự đoán các môn đó
    Media type: application/x-www-form-urlencoded
    POST body:
        course_id: lặp lại, ứng với id các môn học cần dự đoán điểm
        e.g: course_id=7;course_id=8;course_id=9
    :param request:
    :param profile_id:
    :return:
    """
    try:
        student = mainModel.Profiles.objects.get(pk=profile_id)
    except mainModel.Profiles.DoesNotExist:
        result = {"error": "Student don't exist"}
        return Response(result)
    
    grade_predicted = {}
    if request.method == 'POST':
        course_id_list = list(map(int, request.POST.getlist('course_id')))
        predict_list = predict_grade(student, course_id_list=course_id_list, fitting=False, save_history=False)
    else:
        predict_list = mainModel.GradePredicted.objects.filter(student_id=profile_id)

    grade_predicted = {
        pre.course_id: {
            "code": pre.course.courseCode,
            "name": pre.course.courseName,
            "grade_predicted": pre.grade,
        } for pre in predict_list}

    result = {
        "student_id": profile_id,
        "major_id": student.major_id,
        "courses": grade_predicted,
    }
    return Response(result)


def predict_grade_statistic(grade_predicted: mainModel.GradePredicted):
    """ Các thống kê về điểm của môn học và dựa trên điểm dự đoán và các điểm đã có trong dữ liệu
    :param grade_predicted:
    :return:
    """
    avg = 0
    top = 1
    try:
        avg = mainModel.Transcript.objects.filter(course_id=grade_predicted.course_id).aggregate(Avg('grade'))['grade__avg']
        top = mainModel.Transcript.objects.filter(course_id=grade_predicted.course_id, grade__gte=grade_predicted.grade).count()
        top = top / mainModel.Transcript.objects.filter(course_id=grade_predicted.course_id).count()
        top = round(top * 100, 1)
    except Exception as e:
        print("error predict_grade_statistic:", e)

    result = {
        'average grade': avg,
        'grade_top': top,
    }
    return result


def student_predict_loss(student):
    """ Thống kê lại sai số trên các dự đoán điểm đã được thực hiện cho sinh viên đầu vào

    :param student:
    :return:
    """
    # Lấy điểm các môn của sinh viên, tuy nhiên chỉ lấy ở lần đầu học tránh trường hợp học lại điểm được đã cải thiện không còn phù hợp trong việc sử dụng để đánh giá dự đoán
    params = mainModel.Transcript.objects.filter(student=student).values('course_id').annotate(min_semester=Min('semester_id'))
    loss = []
    for param in params:  # param có dạng {'course_id': <int>, 'min_semester': <int>}
        try:
            row = mainModel.Transcript.objects.get(student=student, course_id=param['course_id'], semester_id=param['min_semester'])
            predicts = mainModel.PredictHistory.objects.filter(student=student, course_id=row.course_id)
            for predict in predicts:
                loss.append(row.grade - predict.grade)
        except Exception as e:
            print(e, param)

    num = len(loss)
    loss = np.array(loss)
    mae = np.abs(loss).mean()
    rmse = loss * loss
    rmse = rmse.mean()
    result = {
        'total_predict': num,
        'mae': 0 if np.isnan(mae) else mae,
        'rmse': 0 if np.isnan(rmse) else rmse,
    }

    return result


def model_predict_loss():
    """ Thông kê sai số chung của mô hình dựa trên tất cả các dự đoán đã đưa ra và điểm của sinh viên
    :return:
    """
    student_predicts = mainModel.PredictHistory.objects.values('student').annotate(count=Count('student_id'))

    result = {
        'total_predict': 0,
        'mae': 0,
        'rmse': 0,
    }
    for stu_pre in student_predicts:
        try:
            pre_loss = student_predict_loss(stu_pre['student'])
            result['total_predict'] += pre_loss['total_predict']
            result['mae'] += pre_loss['total_predict'] * pre_loss['mae']
            result['rmse'] += pre_loss['total_predict'] * pre_loss['rmse']
        except Exception as e:
            print(e)
    # print("model_predict_loss:", pre_loss)
    if pre_loss['total_predict'] != 0:
        result['mae'] /= pre_loss['total_predict']
        result['rmse'] /= pre_loss['total_predict']

    return result


@api_view(['GET'])
def get_predict_grade_student(request, profile_id, course_id):
    """ API Dự đoán cho sinh viên đồng thòi cung cấp thống kê về sai số mô hình

    :param request:
    :param profile_id:
    :param course_id:
    :return:
    """
    try:
        student = mainModel.Profiles.objects.get(pk=profile_id)
    except mainModel.Profiles.DoesNotExist:
        result = {"error": "Student don't exist"}
        return Response(result)

    try:
        grade_predicted = mainModel.GradePredicted.objects.get(student_id=profile_id, course_id=course_id)
    except:
        grade_predicted = predict_grade(student, course_id_list=[course_id], fitting=False)
        if len(grade_predicted) == 1 and grade_predicted[0].grade is not None:
            grade_predicted = grade_predicted[0]
        else:
            return Response({"error: can't predict grade of course_id {} for student_id {}".format(course_id, profile_id)})
    # print("get_predict_grade_student:", grade_predicted)
    # sta = predict_grade_statistic(grade_predicted)
    predict_loss = {
        "student": student_predict_loss(student),
        "general": model_predict_loss(),
    }

    result = {
        "course_name": grade_predicted.course.courseName,
        "grade_predicted": grade_predicted.grade,
        "predict_loss" : predict_loss
        }
    # result.update(sta)

    return Response(result)

from rest_framework import status
@api_view(['POST'])
@decorator_from_middleware(AdminOnlyMiddleware)
def predict_grade_generation(request, major_id):
    """Predict grade for all students in a generation with a specify major, base on student grade and recommend semester
     of course
    Dự đoán điểm cho tất cẩ sinh viên thuộc cùng một khóa trong cùng chuyên ngành, dự đoán dựa vào điểm đã có của sinh
     viên và kỳ học được đề xuất của các môn học

    POST: Dự đoán điểm theo khóa học và trả về số lượng điểm đã dự đoán
    POST url: /model_data/<int:major_id>/
    Media type: application/x-www-form-urlencoded
    POST body:
        generation_id: lặp lại, ứng với khóa học sẽ được sử dụng dữ liệu điểm làm dữ liệu huấn luyện
        e.g: generation_id=2;generation_id=3;

    :param request:
    :param major_id: int type, là id chuyên ngành của các sinh viên
    :return:
    """
    try:
        isExistMajor = mainModel.Majors.objects.filter(pk=major_id).exists()
        if isExistMajor is False:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        current_semester = mainModel.get_current_semester()
        # current_semester = mainModel.Semesters.objects.get(pk=3)
        list_generation_id = list(map(int, request.POST.getlist('generation_id')))
        generations = []
        for generation_id in list_generation_id:
            semester_rank = mainModel.semester_rank(generation_id=generation_id, current_semester_id=current_semester.pk)
            if semester_rank is None:
                # go to next generation
                continue
            course_id_list = mainModel.Major_Course.objects.filter(major_id=major_id, semesterRecommended=semester_rank + 1
                                                                ).values_list('course_id', flat=True)

            student_list = mainModel.Profiles.objects.filter(major_id=major_id, group__generation_id=generation_id)

            try:
                fit_model(major_id=major_id)
            except Exception as e:
                Response({"error": e})
            total_delete = 0
            total_predict = 0
            for student in student_list:
                delete_num, model = mainModel.GradePredicted.objects.filter(student=student).delete()
                total_delete += delete_num  # not need
                predict_list = predict_grade(student, current_semester, course_id_list, fitting=False, save_history=True)
                total_predict += len(predict_list)

            generations.append({
                "id": generation_id,
                "deleted": total_delete,
                "predicted": total_predict,
            })

        result = {
            "major_id": major_id,
            "generations": generations
        }
        print('oke', list_generation_id)
        return Response(result)
    except Exception as e:
        return Response(status=status.HTTP_404_NOT_FOUND)

def greatest_scoreCR(student, course_can_learn, k=5):
    """Gợi ý k môn học cho sinh viên từ các môn có id thuốc course_can_learn. các môn được gợi ý dựa trên điểm dự đoán
    của các môn học, những môn có điểm dự đoán cao nhất sẽ được gợi ý. Sẽ không gợi ý môn học mà sinh viên đã học

    :param student:
    :param course_can_learn:
    :param k:
    :return:
    """
    grade_predicted = mainModel.GradePredicted.objects.filter(student=student, course_id__in=course_can_learn)
    course_need_pre = [course_id for course_id in course_can_learn if
                       course_id not in grade_predicted.values_list('course_id', flat=True)]

    if len(course_need_pre) > 0:
        predict_grade(student=student, course_id_list=course_need_pre)

    # Tạo bảng điểm dự đoán
    grade_predicted = mainModel.GradePredicted.objects.filter(student=student, course_id__in=course_can_learn
                                                              ).order_by('-grade')[:k]

    result = grade_predicted.values_list('course_id', flat=True)
    return result


def similar_neighborCR(student, course_can_learn, k=5, sim='cosine'):
    """Gợi ý k môn học cho sinh viên từ các môn có id thuốc course_can_learn. Các môn được gợi ý dựa trên việc các sinh
     viên tương đồng khác có học môn đó hay không. Sẽ không gợi ý môn học mà sinh viên đã học

    :param student:
    :param course_can_learn:
    :param k:
    :param sim:
    :return:
    """
    if sim == 'pearson':
        sim = calculate.pearson_similarity
    else:
        sim = calculate.cosine_similarity

    # normal data
    data = train_data_to_DF(student.major_id)
    data, filled_matrix = process.fillNan(data, type="row_avg")

    # leaned matrix of all student in data
    learned = filled_matrix.astype(int).replace(1, -1).replace(0, 1)

    # clear input data
    student_grade = student_grade_to_DF(student.pk)
    valid_course = list(set(student_grade.columns) & set(data.columns))
    student_grade = student_grade.reindex(columns=valid_course)

    # get recommend course in next semester

    similarity_df = sim(data.reindex(columns=valid_course), student_grade)
    result = (similarity_df.values * learned[course_can_learn]).sum() / len(data)
    return list(result.nlargest(k).index)


@api_view(['GET'])
def course_recommend(request, profile_id, method='greatest', k=5):
    """Gợi ý các môn học cho sinh viên trong kỳ học tới

    :param request:
    :param profile_id:
    :param method: greatest | similar
    :param k:
    :return:
    """
    global MODEL
    # todo: đề xuất các môn học mặc định
    try:
        student = mainModel.Profiles.objects.get(pk=profile_id)
    except Exception:
        return Response({"error": "course_id don't exist"})

    # Lấy các môn học có thể học trong kỳ này
    current_semester = mainModel.get_current_semester()
    semester_rank = mainModel.semester_rank(group_id=student.group_id, current_semester_id=current_semester.pk)
    course_can_learn = mainModel.Major_Course.objects.filter(major_id=student.major_id, semesterRecommended=semester_rank + 1)
    course_can_learn = course_can_learn.values_list('course_id', flat=True)

    if method == 'greatest':
        recommend_course_id = greatest_scoreCR(student, course_can_learn, k)
    else:
        recommend_course_id = similar_neighborCR(student, course_can_learn, k, 'pearson')

    recommended_course = mainModel.Courses.objects.filter(courseID__in=recommend_course_id)

    try:
        recommend_semester = mainModel.Semesters.objects.get(pk=current_semester.pk + 1).semesterName
    except Exception as e:
        recommend_semester = ""
    result = {
        "student_id": profile_id,
        "recommend_semester_id": recommend_semester,
        "course_recommend": {course: {} for course in recommend_course_id}
    }
    for course in recommended_course:
        result["course_recommend"][course.pk] = {
            "course_code": course.courseCode,
            "course_name": course.courseName,
            "credit": course.credit
        }
    return Response(result)

