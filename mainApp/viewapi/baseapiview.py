from rest_framework.decorators import api_view
from rest_framework.response import Response
from mainApp.models import Units, Generations, Majors, Courses, Major_Course, Semesters, StudentGroups, Years
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
@api_view(["GET"])
def list_generations(request, unit_id):
    """
    Lấy ra danh sách khóa của trường unit_id
    """
    result = [{'generationID': gen.generationID,
               'generationName': gen.generationName,
               } for gen in Generations.objects.filter(unit_id=unit_id).order_by('-generationName')
              ]
    return Response(result)

@login_required(login_url='/login/')
@api_view(["GET"])
def list_majors(request, unit_id):
    """
    Lấy danh sách ngành của trường unit_id
    """
    result = [{'majorID': major.majorID,
               'majorName': major.majorName,
               } for major in Majors.objects.filter(unit_id=unit_id)
              ]
    return Response(result)

@login_required(login_url='/login/')
@api_view(["GET"])
def list_groups(request, generation_id):
    """
    Lấy danh sách các lớp của khóa generation_id
    """
    result = [{'groupID': group.groupID,
               'groupName': group.groupName,
               } for group in StudentGroups.objects.filter(generation_id=generation_id).order_by('-groupName')
              ]
    return Response(result)

@login_required(login_url='/login/')
@api_view(["GET"])
def list_semester(request, generation_id):
    """
    Lấy danh sách các ký học của khóa
    """
    year_id = 1
    try:
        year_id = Generations.objects.get(generation_id=generation_id).beginningYear_id
    except:
        print("generation_id don't exsit")

    result = [{'semesterID': sem.semesterID,
               'semesterName': sem.semesterName,
               } for sem in Semesters.objects.filter(year_id__gte=year_id)
              ]
    return Response(result)

@login_required(login_url='/login/')
@api_view(["GET"])
def list_courses(request, major_id):
    """
    Lấy danh sách các môn học thuộc ngành major_id
    """
    result = [{'courseID': courseID,
               'counseCode': counseCode,
               'courseName': courseName,
               } for courseID, counseCode, courseName in Major_Course.objects.filter(major_id=major_id).values_list("course_id", "course__courseCode", "course__courseName")
              ]
    return Response(result)

@login_required(login_url='/login/')
@api_view(["GET"])
def list_years(request, type_sort='only', year_id=0):
    """
    Lấy danh sách các năm học có thứ tự sắp xếp
    """
    if type_sort == 'only':
        result = [{'yearID': year.yearID,
                'yearName': year.yearName,
                } for year in Years.objects.filter(yearID=year_id).order_by('yearName')
                ]
        return Response(result)
    elif type_sort == 'asc':
        result = [{'yearID': year.yearID,
                'yearName': year.yearName,
                } for year in Years.objects.all().order_by('yearName')
                ]
        return Response(result)
    elif type_sort == 'desc':
        result = [{'yearID': year.yearID,
                'yearName': year.yearName,
                } for year in Years.objects.all().order_by('-yearName')
                ]
        return Response(result)
        