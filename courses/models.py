# courses/models.py
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.utils import timezone

# ---------------------------
# Custom user (matches ER diagram)
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Roles.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STUDENT = 'STUDENT', 'Student'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255, blank=True)  # present in ER
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    # required by Django admin/auth
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'

    def __str__(self):
        return f"{self.email} ({self.role})"


# ---------------------------
# Student & Instructor
# ---------------------------
class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    reg_no = models.CharField(max_length=100, unique=True)
    admission_date = models.DateField()
    program = models.CharField(max_length=200)
    current_term = models.IntegerField()

    class Meta:
        db_table = 'student'

    def __str__(self):
        return f"{self.reg_no}"


class Instructor(models.Model):
    instructor_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile', null=True, blank=True)
    employee_no = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = 'instructor'

    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name} ({self.employee_no})"
        return self.employee_no


# ---------------------------
# Department, Course, Term
# ---------------------------
class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'department'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)  # e.g., CS101
    title = models.CharField(max_length=255)
    credits = models.IntegerField()
    dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='courses')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'course'

    def __str__(self):
        return f"{self.code} - {self.title}"


class Term(models.Model):
    term_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)  # e.g., "Fall 2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_enrollment_open = models.BooleanField(default=False)

    class Meta:
        db_table = 'term'

    def __str__(self):
        return self.name


# ---------------------------
# CourseSection & Enrollment
# ---------------------------
class CourseSection(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    section_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='sections')
    section_no = models.CharField(max_length=50)  # e.g., 'A'
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')
    room_text = models.CharField(max_length=200, blank=True)
    timeslot_text = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    add_drop_deadline = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'course_section'
        unique_together = (('course', 'term', 'section_no'),)

    def __str__(self):
        return f"{self.course.code} - {self.term.name} - {self.section_no}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        DROPPED = 'DROPPED', 'Dropped'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    enrollment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)
    grade = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'enrollment'
        unique_together = (('student', 'section'),)

    def __str__(self):
        return f"{self.student.reg_no} -> {self.section} ({self.status})"
