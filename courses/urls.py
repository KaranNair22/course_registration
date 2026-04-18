from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:pk>/register/', views.register_for_course, name='course_register'),

    # authentication & student
    path('account/register/', views.student_signup, name='student_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),

    # instructor
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),

    # admin (custom dashboard & CRUD)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/courses/add/', views.course_create, name='admin_course_create'),
    path('admin/courses/<int:pk>/edit/', views.course_update, name='admin_course_update'),
    path('admin/courses/<int:pk>/delete/', views.course_delete, name='admin_course_delete'),
    path('admin/sections/add/', views.section_create, name='admin_section_create'),
    path('admin/sections/<int:pk>/edit/', views.section_update, name='admin_section_update'),
    path('admin/sections/<int:pk>/delete/', views.section_delete, name='admin_section_delete'),
    # instructor token login + set password
    path('instructor/token-login/<str:token>/', views.instructor_token_login, name='instructor_token_login'),
    path('account/set-password/', views.set_password, name='set_password'),
]




'''from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:pk>/register/', views.register_for_course, name='course_register'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/courses/add/', views.course_create, name='admin_course_create'),
    path('admin/courses/<int:pk>/edit/', views.course_update, name='admin_course_update'),
    path('admin/courses/<int:pk>/delete/', views.course_delete, name='admin_course_delete'),
    path('admin/sections/add/', views.section_create, name='admin_section_create'),
    path('admin/sections/<int:pk>/edit/', views.section_update, name='admin_section_update'),
    path('admin/sections/<int:pk>/delete/', views.section_delete, name='admin_section_delete'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('account/register/', views.student_signup, name='student_signup'),
]
'''