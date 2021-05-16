from django.urls import path
from . import adminviews
from .viewapi import unitview, yearview, semesterview, courseview, majorview, learningputcomeview, generationview, functionview, roleview, groupview
from .viewapi import trainingframeworkview, userview, logs, statisticalview, configmodelview
from .viewapi import baseapiview, predictgrade, suggestcourse, showviewlearningoutcomeview, choicedata

urlpatterns = [
    # ----------------Các url về  người dùng ----------------
    path('user/', userview.userPagination_page, name = 'user'),
    path('user/page<int:num>/limit<int:limit>/', userview.userPagination_page, name = 'userpage'),
    path('user-getlist/<int:offset>/<int:limit>/', userview.user_getListForOffset, name = 'user-getlistOffset'),
    path('user-form/', userview.user_form_create, name = 'user-form'),
    path('user-form/<str:id>/', userview.user_form_update, name = 'user-form-update'),
    # path('user-form/<str:id>/', userview.user_form, name = 'user-form-update'),
    path('user-delete/<str:id>/', userview.user_delete, name = 'user-delete'),
    path('user-export/', userview.export_page, name = 'user-export-page'),
    path('user-permission/', userview.user_permissions, name = 'user-permission'),
    path('user-permission-update/', userview.user_permissions_update, name = 'user-permission-update'),

    # ----------------Các url về  chương trình đào tạo của ngành ----------------
    path('trainingframework/', trainingframeworkview.trainingframeworkPagination_page, name = 'trainingframework'),
    path('trainingframework/page<int:num>/limit<int:limit>/', trainingframeworkview.trainingframeworkPagination_page, name = 'trainingframeworkpage'),
    path('trainingframework-getlist/<int:offset>/<int:limit>/',trainingframeworkview.trainingframework_getListForOffset, name='trainingframework-getlistOffset'),
    path('trainingframework-form/', trainingframeworkview.trainingframework_form, name = 'trainingframework-form'),
    path('trainingframework-form/<str:id>/', trainingframeworkview.trainingframework_form, name = 'trainingframework-form-update'),
    path('trainingframework-delete/<str:id>/', trainingframeworkview.trainingframework_delete, name = 'trainingframework-delete'),
    path('trainingframework-import/', trainingframeworkview.import_page, name = 'trainingframework-import-page'),
    path('trainingframework-export/', trainingframeworkview.export_page, name = 'trainingframework-export-page'),


    # ----------------Các url về  gợi ý môn học ----------------
    path('suggestioncourse/', suggestcourse.suggestioncourse_page, name = 'suggestioncourse'),

    # ----------------Các url về  dự báo điểm ----------------
    path('scoreforecast/', predictgrade.scoreforecast_page, name = 'scoreforecast'),
    path('scoreforecast-generation/', predictgrade.scoreforecast_generation_page, name = 'scoreforecast-generation'),
    path('api/scoreforecast/<int:major>/<int:generation>/', predictgrade.time_scoreforecast_generation_page, name = 'api-scoreforecast'),


    # ----------------Các url về  bảng điểm sinh viên ----------------
    path('viewlearningoutcome/', showviewlearningoutcomeview.viewlearningoutcome, name='viewlearningoutcome'),

    # ----------------Các url về  hồ sơ ----------------
    path('profile/', showviewlearningoutcomeview.viewProfile, name='profile'),
    
    # ----------------Các url về  các thống kê ----------------
    path('statistical/', statisticalview.distribute_transcript, name = 'statistical'),
    path('course-avg/', statisticalview.course_avg_transcript, name = 'course-avg'),
    path('statistical-gpa/', statisticalview.gpa_generation, name = 'statistical-gpa'),
    path('statistical-gpa-student/', statisticalview.gpa_student, name = 'statistical-gpa-student'),

    # ----------------Các url về  chọn mô hình ----------------
    path('configmodel/', configmodelview.get_config_model, name = 'configmodel'),
    path('configmodel/<int:model_id>', configmodelview.post_config_model, name = 'configmodel-post'),

    # ----------------Các url về chọn data để huấn luyện ----------------
    path('choice-data/', choicedata.get_choice_data, name = 'choice-data'),

    # ----------------Các url về  trường ----------------
    path('unit/page<int:num>/limit<int:limit>/', unitview.unitPagination_page, name = 'unitpage'),
    path('unit/', unitview.unitPagination_page, name = 'unit'),
    path('unit-form/', unitview.unit_form, name = 'unit-form'),
    path('unit-form/<str:unit_id>/', unitview.unit_form, name = 'unit-form-update'),
    path('unit-delete/<str:unit_id>/', unitview.unit_delete, name = 'unit-delete'),
    path('unit-getlist/', unitview.unit_getList, name = 'unit-getlist'),
    path('unit-getlist/<int:offset>/<int:limit>/', unitview.unit_getListForOffset, name = 'unit-getlistOffset'),
    path('unit-import/', unitview.import_page, name = 'unit-import-page'),
    path('unit-export/', unitview.export_page, name = 'unit-export-page'),

    # ----------------Các url về  năm học ----------------
    path('year/page<int:num>/limit<int:limit>/', yearview.yearPagination_page, name = 'yearpage'),
    path('year/', yearview.yearPagination_page, name = 'year'),
    path('year-getlist/', yearview.year_getList, name = 'year-getlist'),
    path('year-getlist/<int:offset>/<int:limit>/', yearview.year_getListForOffset, name = 'year-getlistOffset'),
    path('year-form/', yearview.year_form, name = 'year-form'),
    path('year-form/<str:id>/', yearview.year_form, name = 'year-form-update'),
    path('year-delete/<str:id>/', yearview.year_delete, name = 'year-delete'),
    path('year-import/', yearview.import_page, name = 'year-import-page'),
    path('year-export/', yearview.export_page, name = 'year-export-page'),

    # ----------------Các url về  kỳ học ----------------
    path('semester/page<int:num>/limit<int:limit>/', semesterview.semesterPagination_page, name = 'semesterpage'),
    path('semester/', semesterview.semesterPagination_page, name = 'semester'),
    path('semester-getlist/', semesterview.semester_getList, name = 'semester-getlist'),
    path('semester-getlist/<int:offset>/<int:limit>/', semesterview.semester_getListForOffset, name = 'semester-getlistOffset'),
    path('semester-form/', semesterview.semester_form, name = 'semester-form'),
    path('semester-form/<str:id>/', semesterview.semester_form, name = 'semester-form-update'),
    path('semester-delete/<str:id>/', semesterview.semester_delete, name = 'semester-delete'),
    path('semester-import/', semesterview.import_page, name = 'semester-import-page'),
    path('semester-export/', semesterview.export_page, name = 'semester-export-page'),

    # ----------------Các url về  môn học ----------------
    path('course/', courseview.coursePagination_page, name = 'course'),
    path('course/page<int:num>/limit<int:limit>/', courseview.coursePagination_page, name = 'coursepage'),
    path('course-getlist/', courseview.course_getList, name = 'course-getlist'),
    path('course-getlist/<int:offset>/<int:limit>/', courseview.course_getListForOffset, name = 'course-getlistOffset'),
    path('course-form/', courseview.course_form, name = 'course-form'),
    path('course-form/<str:course_id>/', courseview.course_form, name = 'course-form-update'),
    path('course-delete/<str:course_id>/', courseview.course_delete, name = 'course-delete'),
    path('course-import/', courseview.import_page, name = 'course-import-page'),
    path('course-export/', courseview.export_page, name = 'course-export-page'),

    # ----------------Các url về ngành học ----------------
    path('major/page<int:num>/limit<int:limit>/', majorview.majorPagination_page, name = 'majorpage'),
    path('major/', majorview.majorPagination_page, name = 'major'),
    path('major-getlist/', majorview.major_getList, name = 'major-getlist'),
    path('major-getlist/<int:offset>/<int:limit>/', majorview.major_getListForOffset, name = 'major-getlistOffset'),
    path('major-form/', majorview.major_form, name = 'major-form'),
    path('major-form/<str:major_id>/', majorview.major_form, name = 'major-form-update'),
    path('major-delete/<str:major_id>/', majorview.major_delete, name = 'major-delete'),
    path('major-import/', majorview.import_page, name = 'major-import-page'),
    path('major-export/', majorview.export_page, name = 'major-export-page'),

    # ----------------Các url về khóa học ----------------
    path('generation/page<int:num>/limit<int:limit>/', generationview.generationPagination_page, name = 'generationpage'),
    path('generation/', generationview.generationPagination_page, name = 'generation'),
    path('generation-getlist/<int:offset>/<int:limit>/', generationview.generation_getListForOffset, name = 'generation-getlistOffset'),
    path('generation-form/', generationview.generation_form, name = 'generation-form'),
    path('generation-form/<str:generation_id>/', generationview.generation_form, name = 'generation-form-update'),
    path('generation-delete/<str:generation_id>/', generationview.generation_delete, name = 'generation-delete'),
    path('generation-import/', generationview.import_page, name = 'generation-import-page'),
    path('generation-export/', generationview.export_page, name = 'generation-export-page'),

    # ----------------Các url về kết quả học tập sinh viên ----------------
    path('learningoutcome/', learningputcomeview.learningoutcomePagination_page, name = 'learningoutcome'),
    path('learningoutcome/page<int:num>/limit<int:limit>/', learningputcomeview.learningoutcomePagination_page, name = 'learningoutcomepage'),
    path('learningoutcome-import/', learningputcomeview.transcript_file_process, name = 'learningoutcome-import-page'),
    path('learningoutcome-getlist/<int:offset>/<int:limit>/', learningputcomeview.transcript_getListForOffset, name = 'learningoutcome-getlistOffset'),
    path('learningoutcome-form/', learningputcomeview.transcript_form, name = 'learningoutcome-form'),
    path('learningoutcome-form/<str:id>/', learningputcomeview.transcript_form, name = 'learningoutcome-form-update'),
    path('learningoutcome-delete/<str:id>/', learningputcomeview.transcript_delete, name = 'learningoutcome-delete'),
    path('learningoutcome-export/', learningputcomeview.export_page, name = 'learningoutcome-export-page'),

    # ----------------Các url về chức năng ----------------
    path('function/', functionview.functionPagination_page, name = 'function'),
    path('function/page<int:num>/limit<int:limit>/', functionview.functionPagination_page, name = 'functionpage'),
    path('function-getlist/<int:offset>/<int:limit>/', functionview.function_getListForOffset, name = 'function-getlistOffset'),
    path('function-form/', functionview.function_form, name = 'function-form'),
    path('function-form/<str:id>/', functionview.function_form, name = 'function-form-update'),
    path('function-delete/<str:id>/', functionview.function_delete, name = 'function-delete'),
    path('function-import/', functionview.import_page, name = 'function-import-page'),
    path('function-export/', functionview.export_page, name = 'function-export-page'),

    # ----------------Các url về vai trò ----------------
    path('role/', roleview.rolePagination_page, name = 'role'),
    path('role/page<int:num>/limit<int:limit>/', roleview.rolePagination_page, name = 'rolepage'),
    path('role-getlist/<int:offset>/<int:limit>/', roleview.role_getListForOffset, name = 'role-getlistOffset'),
    path('role-form/', roleview.role_form_new, name = 'role-form'),
    path('role-form/<str:id>/', roleview.role_form_update_new, name = 'role-form-update'),
    path('role-delete/<str:id>/', roleview.role_delete, name = 'role-delete'),
    path('role-import/', roleview.import_page_new, name = 'role-import-page'),
    path('role-export/', roleview.export_page, name = 'role-export-page'),

    # ----------------Các url về lớp ----------------
    path('group/', groupview.groupPagination_page, name = 'group'),
    path('group/page<int:num>/limit<int:limit>/', groupview.groupPagination_page, name = 'grouppage'),
    path('group-getlist/<int:offset>/<int:limit>/', groupview.group_getListForOffset, name = 'group-getlistOffset'),
    path('group-form/', groupview.group_form, name = 'group-form'),
    path('group-form/<str:group_id>/', groupview.group_form, name = 'group-form-update'),
    path('group-delete/<str:group_id>/', groupview.group_delete, name = 'group-delete'),
    path('group-import/', groupview.import_page, name = 'group-import-page'),
    path('group-export/', groupview.export_page, name = 'group-export-page'),

    # ----------------Các url về ghi log ----------------
    path('logs/', logs.logPagination_page, name = 'logs'),
    path('logs/page<int:num>/limit<int:limit>/', logs.logPagination_page, name = 'logspage'),
    path('logs-getlist/<int:offset>/<int:limit>/', logs.log_page, name = 'logs-getlistOffset'),
    path('logs-delete/', logs.delete_log, name = 'logs-delete'),

    # ----------------Các url về api các danh sách để sử trong thống kê ----------------
    path('base-list/generations/<int:unit_id>', baseapiview.list_generations),
    path('base-list/majors/<int:unit_id>', baseapiview.list_majors),
    path('base-list/groups/<int:generation_id>', baseapiview.list_groups),
    path('base-list/semesters/<int:generation_id>', baseapiview.list_semester),
    path('base-list/courses/<int:major_id>', baseapiview.list_courses),
    path('base-list/years/<str:type_sort>/<int:year_id>', baseapiview.list_years),

]