import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date

from courses.models import Department, Term, Course, CourseSection, Instructor


class Command(BaseCommand):
    help = 'Seed departments, terms, courses and sections from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to courses JSON file')

    def handle(self, *args, **options):
        p = Path(options['json_file'])
        if not p.exists():
            self.stderr.write(f'File not found: {p}')
            return

        data = json.loads(p.read_text(encoding='utf-8'))
        created = {'departments': 0, 'terms': 0, 'courses': 0, 'sections': 0}

        # Departments
        for d in data.get('departments', []):
            dept, c = Department.objects.get_or_create(code=d['code'], defaults={'name': d.get('name', d['code'])})
            if c:
                created['departments'] += 1
                self.stdout.write(self.style.SUCCESS(f'Created department {dept.code}'))

        # Terms
        for t in data.get('terms', []):
            term, c = Term.objects.get_or_create(name=t['name'], defaults={
                'start_date': parse_date(t['start_date']),
                'end_date': parse_date(t['end_date']),
                'is_enrollment_open': t.get('is_enrollment_open', False),
            })
            if c:
                created['terms'] += 1
                self.stdout.write(self.style.SUCCESS(f'Created term {term.name}'))

        # Courses
        for c in data.get('courses', []):
            dept = None
            if c.get('dept'):
                try:
                    dept = Department.objects.get(code=c['dept'])
                except Department.DoesNotExist:
                    self.stderr.write(f"Department {c['dept']} not found for course {c['code']}")
            course, created_flag = Course.objects.get_or_create(code=c['code'], defaults={
                'title': c.get('title', ''),
                'credits': c.get('credits', 0),
                'dept': dept,
                'is_active': c.get('is_active', True),
            })
            if created_flag:
                created['courses'] += 1
                self.stdout.write(self.style.SUCCESS(f'Created course {course.code}'))

        # Sections
        for s in data.get('sections', []):
            try:
                course = Course.objects.get(code=s['course'])
            except Course.DoesNotExist:
                self.stderr.write(f"Course {s['course']} not found for section {s.get('section_no')}")
                continue

            try:
                term = Term.objects.get(name=s['term'])
            except Term.DoesNotExist:
                self.stderr.write(f"Term {s['term']} not found for section {s.get('section_no')}")
                continue

            instructor = None
            emp_no = s.get('instructor_employee_no')
            if emp_no:
                try:
                    instructor = Instructor.objects.get(employee_no=emp_no)
                except Instructor.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Instructor {emp_no} not found, leaving blank'))

            section, created_flag = CourseSection.objects.get_or_create(
                course=course,
                term=term,
                section_no=s.get('section_no', 'A'),
                defaults={
                    'instructor': instructor,
                    'room_text': s.get('room_text', ''),
                    'timeslot_text': s.get('timeslot_text', ''),
                    'capacity': s.get('capacity', 0),
                    'status': s.get('status', CourseSection.Status.PLANNED),
                }
            )
            if created_flag:
                created['sections'] += 1
                self.stdout.write(self.style.SUCCESS(f'Created section {section}'))

        self.stdout.write(self.style.SUCCESS(f"Seeding complete: {created}"))
