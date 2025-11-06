# courses/admin.py
from django.contrib import admin
from .models import (
    User, Student, Instructor, Department,
    Course, Term, CourseSection, Enrollment
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email',)
    list_filter = ('role', 'is_active')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('reg_no', 'user', 'program', 'current_term', 'admission_date')
    search_fields = ('reg_no', 'user__email')

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('employee_no', 'user', 'title')
    search_fields = ('employee_no', 'user__email')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'dept', 'credits', 'is_active')
    search_fields = ('code', 'title')
    list_filter = ('dept', 'is_active')

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_enrollment_open')

@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'term', 'section_no', 'instructor', 'capacity', 'status')
    search_fields = ('course__code', 'section_no')
    list_filter = ('term', 'status')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'status', 'enrolled_at', 'grade')
    search_fields = ('student__reg_no', 'section__course__code')
    list_filter = ('status',)
