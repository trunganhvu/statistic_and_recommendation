# statistic views
import numpy as np
from django.http import HttpResponseRedirect
from statistic import lib
from mainApp import models as mainModel
from django.db.models import Avg, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.utils.decorators import decorator_from_middleware
from .middlewares import GPAMiddleware


@api_view(['GET'])
def get_distribute(request, unit_id=None, generation_id=None, major_id=0, sem_start=None, sem_end=None, course_id=0, boundary_type='a-f'):
    """ API trả về thống kê số lượng điểm sinh viên theo từng khoảng định trước
    URL: statistic/distribute/<int:unit_id>/<int:generation_id>/<int:major_id>/<int:course_id>/<str:boundary_type>/<int:sem_start>/<int:sem_end>

    :param request:
    :param unit_id: bắt buộc, là id của trường, nếu để 0 thì sẽ là tất cả các trường
    :param generation_id: bắt buộc, là id cua các khóa, nếu để 0 thì sẽ là tất cả các khóa
    :param major_id: là id chuyên ngành, bắt buộc có, nếu để 0 thì sẽ là tất cả các ngành
    :param sem_start: id của semester đầu tiên muốn thống kê, không bắt buộc
    :param sem_end: id của semester cuối cùng muốn thống kê, không bắt buộc
    :param course_id: id của môn học muốn thống kê, bắt buộc có, nếu để 0 thì sẽ là tất cả các môn
    :param boundary_type: có 3 thang phân chia điểm là a-f, 10 và 20
    :return:
    """
    data = mainModel.Transcript.objects.select_related('student')
    if unit_id > 0:
        data = data.filter(student__group__generation__unit_id=unit_id)
    if generation_id > 0:
        data = data.filter(student__group__generation_id=generation_id)
    else:
        data = data.all()
    if major_id > 0:
        data = data.filter(student__major_id=major_id)

    if course_id > 0:
        data = data.filter(course_id=course_id)
    if sem_start is not None and sem_end is not None:
        data = data.filter(semester_id__gte=sem_start, semester_id__lte=sem_end)

    data = data.values('grade')
    data = [d['grade'] for d in data]

    if boundary_type == '10':
        boundary = {str(i): i for i in range(0, 10, 1)}
    elif boundary_type == '20':
        boundary = {str(i): i for i in np.arange(0, 10, 0.5)}
    else:
        boundary = {'F': 0.0,
                    'D': 4.0,
                    'C': 5.5,
                    'B': 7.0,
                    'A': 8.5}
    dist, statistics = lib.distribute_and_statistic(data, list(boundary.values()))
    result = {
        'unit_id': unit_id,
        'generation_id': generation_id,
        'major_id': major_id if major_id > 0 else 'all',
        'course_id': course_id if course_id > 0 else 'all',
        'boundary_type': boundary_type,
        'sem_start': sem_start,
        'sem_end': sem_end,
        'number_of_grade': len(data),
        'grade_distribute': dict(zip(boundary.keys(), dist)),
        'statistics': {
            'avg': None if statistics[0] is None else round(statistics[0], 2),
            'min': round(statistics[1], 2),
            'q1': round(statistics[2], 2),
            'q2': round(statistics[3], 2),
            'q3': round(statistics[4], 2),
            'max': round(statistics[5], 2),
        }
    }

    return Response(result)


@api_view(['GET'])
def average_grade_of_course(request, course_id, year_start=None, year_end=None):
    """API tính và trả về điểm trung bình của một môn học theo các năm học
    URL: statistic/course_avg/<int:course_id>/<int:year_start>/<int:year_end>

    :param request:
    :param course_id: id của môn học muốn tính điểm trung bình
    :param year_start: năm đầu tiên trong các năm cần tính điểm trung bình, không bát buộc
    :param year_end: năm cuối cùng trong các năm cần tính điểm trung bình, không bát buộc
    :return:
    """
    try:
        course = mainModel.Courses.objects.get(pk=course_id)
    except Exception:
        return Response({"error": "course_id don't exist"})
    result = {
        "course_id": course_id,
        "course_code": course.courseCode,
        "course_name": course.courseName,
        "year": {}
    }
    grade_list = mainModel.Transcript.objects.filter(course_id=course_id)
    if year_start is not None and year_end is not None:
         grade_list.filter(semester__year_id__gte=year_start, semester__year_id__lte=year_end)

    grade_list = grade_list.order_by('semester_id')
    avg_grade_list = grade_list.values('semester__year__yearName').annotate(Avg('grade'), Count('transcriptID'))

    for avg_grade in avg_grade_list:
        result["year"][avg_grade['semester__year__yearName']] = {
            "avg_grade": round(avg_grade['grade__avg'], 2),
            "num_of_grade": avg_grade['transcriptID__count']
        }
    return Response(result)


def calculate_student_gpa(student, method='update'):
    """
    Thực hiện tính toán điểm GPA của sinh viên. GPA sẽ được tính theo GPA trong một kỳ và GPA đến thời điểm đó của từng kỳ học.
    Trả về số lượng bản ghi được tạo ra và bị thay đổi trong cơ sở dữ liệu
    :param student:
    :param method: ['update', 'reevaluation']
    :return:
    """
    update = 0
    create = 0
    student_grade = mainModel.Transcript.objects.filter(student=student).values_list('semester_id', 'course_id', 'course__credit', 'grade')
    if len(student_grade) <= 0:
        return update, create

    if method in ['update', 'reevaluation']:
        student_grade = np.array([list(grade) for grade in student_grade])
        student_grade = student_grade[student_grade[:, 0].argsort()]

        sem_list = np.unique(student_grade[:, 0])
        if method == 'update':
            exist_gpa = mainModel.GPA.objects.filter(student=student)
            exist_sem = exist_gpa.values_list('semester', flat=True)
            sem_list = [sem for sem in sem_list if sem not in exist_sem]
            del exist_gpa, exist_sem

        if len(sem_list) > 0:
            begin_semester_id = mainModel.Semesters.objects.filter(year_id=student.group.generation.beginningYear_id).first().pk

            for sem in sem_list:
                # calculate semesterGpa, GPA in one semester
                sem_data = student_grade[student_grade[:, 0] == sem]
                sem_grade = sem_data[:, 3]
                sem_credit = sem_data[:, 2]
                sem_gpa = round(np.sum(sem_grade * sem_credit) / sum(sem_credit), 2)

                # calculate currentGpa, GPA from fist semester to this semester
                course_set = set([])
                gpa = 0
                total_credit = 0
                for sem_id, cou, credit, grade in student_grade[::-1]:
                    if sem_id <= sem and cou not in course_set:
                        gpa += grade*credit
                        total_credit += credit
                        course_set.add(cou)
                current_gpa = round(gpa / total_credit, 2)
                semesterRank = mainModel.semester_rank(current_semester_id=sem, semester_id=begin_semester_id)
                obj, created = mainModel.GPA.objects.update_or_create(student=student, semester_id=sem,
                                                    defaults={"semesterRank": semesterRank,
                                                              "semesterGpa": sem_gpa,
                                                              "currentGpa": current_gpa})
                if created:
                    create += 1
                else:
                    update += 1

    return update, create


@api_view(['GET'])
def student_gpa(request, profile_id, method='get'):
    """API tính và trả về điểm GPA của sinh viên theo kỳ vả theo quá trình từ đầu đến kỳ học đó
    URL: statistic/gpa/student<int:profile_id>/<str:method>

    :param request:
    :param profile_id: id của sinh viên muốn tính điểm GPA
    :param method: là hành động cần thực hiện là một trong các chuõi sau [get, update, reevaluation].
    get: là lấy GPA của tất cả các kỳ đã tính
    update: sẽ tính GPA ở các kỳ còn thiếu rồi đưa ra GPA của tất cả kỳ. Nên gọi sau khi cập nhập điẻm và sang kỳ học mới
    reevaluation: sẽ tính lại GPA ở tất các kỳ học của sinh viên rồi đưa ra
    :return:
    """
    try:
        student = mainModel.Profiles.objects.get(pk=profile_id)
    except Exception:
        return Response({"error": "profile_id {} don't exist".format(profile_id)})

    if method in ['update', 'reevaluation']:
        calculate_student_gpa(student, method)
    elif method != 'get':
        return HttpResponseRedirect('/statistic/gpa/student/{}/get'.format(profile_id))

    gpa = mainModel.GPA.objects.filter(student=student).order_by('semesterRank')
    result = {
        "student_info": {
            "id": profile_id,
            "unit_id": student.major.unit_id,
            "generation_id": student.group.generation_id,
            "major_id": student.major_id,
        },
        "semester_number": {}
    }

    for sem in gpa:
        result["semester_number"][sem.semesterRank] = {
            "semester_id": sem.semester_id,
            "semesterGpa": sem.semesterGpa,
            "currentGpa": sem.currentGpa
        }

    return Response(result)


@api_view(['GET'])
@decorator_from_middleware(GPAMiddleware)
def gpa(request, unit_id, major_id, generation_id, method='get'):
    """API tính và thống kê điểm GPA của các sinh viên theo kỳ vả theo quá trình từ đầu đến kỳ học đó, sinh viên được
    chọn để tính hay thống kê dựa vào các thông số unit_id, major_id, generation_id trên url
    URL: statistic/gpa/<int:unit_id>/<int:major_id>/<int:generation_id>/<str:method>

    :param request:
    :param unit_id: id của trường, nếu để 0 thì sẽ là tất cả các trường
    :param major_id: id của ngành, nếu để 0 thì sẽ là tất cả các ngành
    :param generation_id: id của khóa, nếu để 0 thì sẽ là tất cả các khóa
    :param method: là hành động cần thực hiện là một trong các chuõi sau [get, update, reevaluation].
    get: là lấy GPA của tất cả các kỳ đã tính
    update: sẽ tính GPA ở các kỳ còn thiếu rồi đưa ra số GPA đã thay đổi
    reevaluation: sẽ tính lại GPA ở tất các kỳ học của rồi đưa ra kết quả số GPA đã thay đổi
    :return:
    """
    result = {
        "major_id": major_id,
        "generation_id": generation_id,
    }

    student_list = mainModel.Profiles.objects
    if unit_id > 0:
        student_list = student_list.filter(group__generation__unit_id=unit_id)
    if major_id > 0:
        student_list = student_list.filter(major_id=major_id)
    if generation_id > 0:
        student_list = student_list.filter(group__generation_id= generation_id)

    student_list = student_list.order_by("-MSSV")

    if method in ["update", "reevaluation"]:
        update = 0
        create = 0
        for student in student_list:
            updated, created = calculate_student_gpa(student, method)
            update += updated
            create += created

        result["updated"] = update
        result["created"] = create

        return Response(result)

    if method != "get":
        return HttpResponseRedirect('/statistic/gpa/{}/{}/{}/get'.format(unit_id, major_id, generation_id))

    result["semester_number"] = {}
    gpa = mainModel.GPA.objects.filter(student__in=student_list)

    sem_rank_list = list(set(gpa.values_list('semesterRank', flat=True)))
    sem_rank_list.sort()

    for sem_rank in sem_rank_list:
        sem_gpa = gpa.filter(semesterRank=sem_rank)

        total_sg = sem_gpa[0].semesterGpa
        max_sg = total_sg
        min_sg = total_sg

        total_cg = sem_gpa[0].currentGpa
        max_cg = total_cg
        min_cg = total_cg

        for row in sem_gpa[1:]:
            total_sg += row.semesterGpa
            if row.semesterGpa > max_sg:
                max_sg = row.semesterGpa
            elif row.semesterGpa < min_sg:
                min_sg = row.semesterGpa

            total_cg += row.currentGpa
            if row.currentGpa > max_cg:
                max_cg = row.currentGpa
            elif row.currentGpa < min_cg:
                min_cg = row.currentGpa

        avg_sg = total_sg / len(sem_gpa)
        avg_cg = total_cg / len(sem_gpa)


        result["semester_number"][sem_rank] = {"semesterGpa": {"max": max_sg,
                                                                     "min": min_sg,
                                                                     "avg": round(avg_sg, 2)
                                                                    },
                                                    "currentGpa": {"max": max_cg,
                                                                    "min": min_cg,
                                                                    "avg": round(avg_cg, 2)
                                                                   }
                                                    }
    return Response(result)
