from django.contrib import admin
from django.urls import path, include
from courses import views as courses_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls', namespace='courses')),
    path('admin/dashboard/', courses_views.admin_dashboard, name='admin_dashboard'),
]

