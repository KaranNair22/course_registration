from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings

from .models import (
	Course, CourseSection, Enrollment, Student, Instructor, User,
)
from .forms import CourseForm, CourseSectionForm


class CourseListView(generic.ListView):
	model = Course
	template_name = "courses/course_list.html"
	context_object_name = "courses"
	paginate_by = 12

	def get_queryset(self):
		qs = super().get_queryset().select_related('dept')
		q = self.request.GET.get('q')
		if q:
			qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
		return qs.order_by('code')


class CourseDetailView(generic.DetailView):
	model = Course
	template_name = "courses/course_detail.html"
	context_object_name = "course"


def _ensure_student_profile(user):
	"""Return a Student instance for this user, creating a minimal profile if missing.

	We create a simple reg_no based on the user id to satisfy the model constraint.
	"""
	if not hasattr(user, 'student_profile') or user.student_profile is None:
		# create a minimal student profile with sensible defaults
		reg_no = f"REG{user.user_id or user.pk or int(timezone.now().timestamp())}"
		student = Student.objects.create(
			user=user,
			reg_no=reg_no,
			admission_date=timezone.now().date(),
			program='Undeclared',
			current_term=1,
		)
		return student
	return user.student_profile


@login_required
def register_for_course(request, pk):
	course = get_object_or_404(Course, pk=pk)

	# find an open section with seats
	section = CourseSection.objects.filter(course=course, status=CourseSection.Status.OPEN).order_by('term__start_date').first()
	if section:
		# check seats
		if section.seats_remaining() <= 0:
			section = None

	if request.method == 'POST':
		# POST: attempt to enroll the logged-in user
		student = _ensure_student_profile(request.user)
		if section is None:
			messages.error(request, 'No open section with available seats for this course.')
			return redirect('courses:course_detail', pk=course.pk)

		# avoid duplicate enrollments (unique constraint)
		enrollment, created = Enrollment.objects.get_or_create(
			student=student,
			section=section,
			defaults={'status': Enrollment.Status.ENROLLED}
		)
		if created:
			messages.success(request, f'You have been registered for {course.code} (section {section.section_no}).')
		else:
			# if previously dropped, allow reenroll
			if enrollment.status != Enrollment.Status.ENROLLED:
				enrollment.status = Enrollment.Status.ENROLLED
				enrollment.enrolled_at = timezone.now()
				enrollment.save()
				messages.success(request, f'Your registration for {course.code} has been updated.')
			else:
				messages.info(request, 'You are already enrolled in this section.')

		return redirect('courses:student_dashboard')

	# GET: show quick register form
	return render(request, 'courses/register_form.html', {'course': course, 'section': section})


def student_signup(request):
	"""Create a user account (minimal) and a linked Student profile.

	The signup form in templates only collects first_name, last_name, email and password.
	We create a minimal Student record so other flows (dashboard, register) work.
	"""
	next_url = request.GET.get('next') or request.POST.get('next') or reverse('courses:student_dashboard')

	if request.method == 'POST':
		email = request.POST.get('email')
		password = request.POST.get('password')
		first_name = request.POST.get('first_name', '').strip()
		last_name = request.POST.get('last_name', '').strip()

		if not email or not password:
			messages.error(request, 'Email and password are required.')
			return render(request, 'courses/signup.html', {'next': next_url})

		# create user
		user = User.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
		user.role = User.Roles.STUDENT
		user.save()

		# create minimal student profile
		reg_no = f"REG{user.user_id or user.pk}"
		Student.objects.create(
			user=user,
			reg_no=reg_no,
			admission_date=timezone.now().date(),
			program='Undeclared',
			current_term=1,
		)

		# log the user in and redirect
		login(request, user)
		messages.success(request, 'Account created and you are now logged in.')
		return redirect(next_url)

	return render(request, 'courses/signup.html', {'next': next_url})


def login_view(request):
	next_url = request.GET.get('next') or request.POST.get('next') or reverse('courses:course_list')
	if request.method == 'POST':
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			login(request, user)
			return redirect(next_url)
	else:
		form = AuthenticationForm(request)
	return render(request, 'courses/login.html', {'auth_form': form, 'next': next_url})


def logout_view(request):
	logout(request)
	messages.info(request, 'You have been logged out.')
	return redirect('courses:course_list')


@login_required
def student_dashboard(request):
	student = _ensure_student_profile(request.user)
	enrollments = student.enrollments.select_related('section__course', 'section__term').all()
	return render(request, 'courses/student_dashboard.html', {'enrollments': enrollments})


@login_required
def instructor_dashboard(request):
	# staff/admins see the admin dashboard; instructors see their sections
	if request.user.is_staff or request.user.role == User.Roles.ADMIN:
		courses = Course.objects.all().select_related('dept')[:200]
		sections = CourseSection.objects.all().select_related('course', 'term')[:200]
		return render(request, 'courses/admin_dashboard.html', {'courses': courses, 'sections': sections})

	# instructor view
	if hasattr(request.user, 'instructor_profile') and request.user.instructor_profile:
		instructor = request.user.instructor_profile
		sections = instructor.sections.select_related('course', 'term').all()
		return render(request, 'courses/admin_dashboard.html', {'courses': [], 'sections': sections})

	messages.error(request, 'You do not have access to the instructor dashboard.')
	return redirect('courses:course_list')
    
@login_required
def admin_dashboard(request):
	# only staff/admins
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'You do not have access to the admin dashboard.')
		return redirect('courses:course_list')

	courses = Course.objects.all().select_related('dept')[:200]
	sections = CourseSection.objects.all().select_related('course', 'term')[:200]
	return render(request, 'courses/admin_dashboard.html', {'courses': courses, 'sections': sections})


# --- token login / set password flow for instructors ---
TOKEN_SALT = 'instructor-login-salt'

def generate_login_token(user):
	"""Create a signed token for a user. Expires are enforced when loading."""
	return dumps({'user_pk': user.pk}, salt=TOKEN_SALT)


def instructor_token_login(request, token):
	"""View to authenticate a user via a signed token and redirect to set password."""
	try:
		data = loads(token, salt=TOKEN_SALT, max_age=60 * 60 * 24)
	except SignatureExpired:
		messages.error(request, 'This login link has expired.')
		return redirect('courses:login')
	except BadSignature:
		messages.error(request, 'Invalid login link.')
		return redirect('courses:login')

	user = get_object_or_404(User, pk=data.get('user_pk'))
	if not user.is_active:
		messages.error(request, 'User account is not active.')
		return redirect('courses:login')

	# log the user in
	login(request, user)
	# mark session so the set-password view knows this is a fresh token login
	request.session['token_login'] = True
	return redirect('courses:set_password')


@login_required
def set_password(request):
	"""Allow a logged-in user (via token) to set their password without the old password."""
	# make sure this was reached via token login or admin
	if not request.user.is_authenticated:
		return redirect('courses:login')

	# Optionally require token_login in session for extra safety
	# allow admins to change without token
	if not request.session.get('token_login') and not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'You are not authorized to set password here.')
		return redirect('courses:course_list')

	if request.method == 'POST':
		form = SetPasswordForm(request.user, request.POST)
		if form.is_valid():
			form.save()
			# clear token flag
			request.session.pop('token_login', None)
			messages.success(request, 'Your password has been set. You are now logged in.')
			return redirect('courses:student_dashboard')
	else:
		form = SetPasswordForm(request.user)

	return render(request, 'courses/set_password.html', {'form': form})

@login_required
def course_create(request):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	if request.method == 'POST':
		form = CourseForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Course created.')
			return redirect('courses:admin_dashboard')
	else:
		form = CourseForm()
	return render(request, 'courses/course_form.html', {'form': form})

@login_required
def course_update(request, pk):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	course = get_object_or_404(Course, pk=pk)
	if request.method == 'POST':
		form = CourseForm(request.POST, instance=course)
		if form.is_valid():
			form.save()
			messages.success(request, 'Course updated.')
			return redirect('courses:admin_dashboard')
	else:
		form = CourseForm(instance=course)
	return render(request, 'courses/course_form.html', {'form': form, 'course': course})

@login_required
def course_delete(request, pk):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	course = get_object_or_404(Course, pk=pk)
	if request.method == 'POST':
		course.delete()
		messages.success(request, 'Course deleted.')
		return redirect('courses:admin_dashboard')
	return render(request, 'courses/course_confirm_delete.html', {'course': course})

@login_required
def section_create(request):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	if request.method == 'POST':
		form = CourseSectionForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Section created.')
			return redirect('courses:admin_dashboard')
	else:
		form = CourseSectionForm()
	return render(request, 'courses/section_form.html', {'form': form})

@login_required
def section_update(request, pk):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	section = get_object_or_404(CourseSection, pk=pk)
	if request.method == 'POST':
		form = CourseSectionForm(request.POST, instance=section)
		if form.is_valid():
			form.save()
			messages.success(request, 'Section updated.')
			return redirect('courses:admin_dashboard')
	else:
		form = CourseSectionForm(instance=section)
	return render(request, 'courses/section_form.html', {'form': form, 'section': section})

@login_required
def section_delete(request, pk):
	if not (request.user.is_staff or request.user.role == User.Roles.ADMIN):
		messages.error(request, 'Permission denied.')
		return redirect('courses:admin_dashboard')

	section = get_object_or_404(CourseSection, pk=pk)
	if request.method == 'POST':
		section.delete()
		messages.success(request, 'Section deleted.')
		return redirect('courses:admin_dashboard')
	return render(request, 'courses/section_confirm_delete.html', {'section': section})

