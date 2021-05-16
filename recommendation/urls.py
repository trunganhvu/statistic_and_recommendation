# recommendation urls
from django.urls import path, include
# from django.views.generic import TemplateView
from recommendation import views

urlpatterns = [
    # Các URLs quản lý dự việc dự đoán điểm môn học cho sinh viên
    path('predict_grade/generation/<int:major_id>', views.predict_grade_generation),
    path('predict_grade/student/<int:profile_id>', views.predict_grade_student),
    path('predict_grade/student/<int:profile_id>/<int:course_id>', views.get_predict_grade_student),

    # Các URLs quản lý mô hình dự đoán và gợi ý
    path('model_data', views.create_train_data_file),
    path('model_data/<int:major_id>', views.create_train_data_file),

    # URL gợi ý môn học cho kỳ tới
    path('course/<int:profile_id>/<str:method>/<int:k>', views.course_recommend),
]
