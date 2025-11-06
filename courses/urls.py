from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:pk>/register/', views.register_for_course, name='course_register'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
]
