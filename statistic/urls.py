# statistic urls
from django.urls import path
from statistic import views

urlpatterns = [
    # url thống kê phân phối của điểm
    path('distribute/<int:unit_id>/<int:generation_id>/<int:major_id>/<int:course_id>/<str:boundary_type>/<int:sem_start>/<int:sem_end>', views.get_distribute),
    path('distribute/<int:unit_id>/<int:generation_id>/<int:major_id>/<int:course_id>/<str:boundary_type>', views.get_distribute),

    # url thống kê trung bình của điểm
    path('course_avg/<int:course_id>/<int:year_start>/<int:year_end>', views.average_grade_of_course),
    path('course_avg/<int:course_id>', views.average_grade_of_course),

    # url thống kê điểm GPA
    path('gpa/student/<int:profile_id>/<str:method>', views.student_gpa),
    path('gpa/<int:unit_id>/<int:major_id>/<int:generation_id>/<str:method>', views.gpa),

]

