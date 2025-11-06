from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Course, CourseSection, Student, Enrollment, User

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    queryset = Course.objects.select_related('dept').all()

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

def register_for_course(request, pk):
    """
    Simple register flow:
    - Accepts POST with 'email' (and optional name)
    - Creates Student user/profile if not exists
    - Enrolls student into the section (first OPEN section of that course in current term) or shows message
    """
    course = get_object_or_404(Course, pk=pk)

    # choose a section: first OPEN section in any term (you can change selection logic)
    section = CourseSection.objects.filter(course=course, status='OPEN').order_by('term__start_date').first()

    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name', '')
        if not email:
            messages.error(request, "Please provide an email.")
            return redirect('courses:course_detail', pk=course.pk)

        # create or get User & Student
        user, created = User.objects.get_or_create(email=email, defaults={'first_name': name or '', 'role': User.Roles.STUDENT})
        if created:
            user.set_password('changeme123')   # placeholder password; encourage user to reset
            user.save()
        student, _ = Student.objects.get_or_create(user=user, defaults={'reg_no': f'R{user.user_id:05d}', 'admission_date': '2025-06-01', 'program': 'Unknown', 'current_term': 1})

        if section is None:
            messages.error(request, "No open sections are available for this course. Please contact admin.")
            return redirect('courses:course_detail', pk=course.pk)

        # check unique enrollment
        if Enrollment.objects.filter(student=student, section=section).exists():
            messages.info(request, "You are already enrolled in this section.")
            return redirect('courses:course_detail', pk=course.pk)

        # capacity check
        taken = Enrollment.objects.filter(section=section, status='ENROLLED').count()
        if section.capacity and taken >= section.capacity:
            # create waitlist? Here we mark as DROPPED or show waitlist message.
            Enrollment.objects.create(student=student, section=section, status='DROPPED')  # optional behavior
            messages.warning(request, "Section is full. You have been added as dropped/waitlist. Admin will confirm.")
            return redirect('courses:course_detail', pk=course.pk)

        # create enrollment
        Enrollment.objects.create(student=student, section=section, status='ENROLLED')
        messages.success(request, "Registration successful! Check your status in the dashboard.")
        return redirect('courses:student_dashboard')

    return render(request, 'courses/register_form.html', {'course': course, 'section': section})


@login_required(login_url='/admin/login/?next=/')   # you can change login_url or remove decorator
def student_dashboard(request):
    """
    Simple dashboard: shows enrollments for logged-in student.
    """
    # get student profile for logged-in user
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.info(request, "No student profile found for your account.")
        return render(request, 'courses/student_dashboard.html', {'enrollments': []})

    enrollments = student.enrollments.select_related('section__course', 'section__term').all()
    return render(request, 'courses/student_dashboard.html', {'enrollments': enrollments})
