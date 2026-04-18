import json
import csv
import secrets
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

from courses.models import Instructor

User = get_user_model()

# token generation mirrors views.TOKEN_SALT
TOKEN_SALT = 'instructor-login-salt'
from django.core.signing import dumps


class Command(BaseCommand):
    help = 'Import instructors from a JSON file and emit one-time login URLs.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument('--out', type=str, default='instructor_tokens.csv', help='CSV output file')
        parser.add_argument('--base-url', type=str, default='http://127.0.0.1:8000', help='Base URL for generated token links')

    def handle(self, *args, **options):
        p = Path(options['json_file'])
        if not p.exists():
            self.stderr.write(f'File not found: {p}')
            return

        data = json.loads(p.read_text(encoding='utf-8'))
        out_rows = []

        for item in data:
            email = item.get('user__email')
            first = item.get('user__first_name', '')
            last = item.get('user__last_name', '')
            employee_no = item.get('employee_no')
            title = item.get('title', '')

            if not email:
                # generate placeholder
                email = f'instructor+{secrets.token_hex(4)}@example.local'

            # create or get user with unusable password
            user, created = User.objects.get_or_create(email=email, defaults={'first_name': first, 'last_name': last})
            if created:
                # user manager will set unusable password if password is None
                user.set_unusable_password()
                # mark role if Role exists
                try:
                    user.role = User.Roles.INSTRUCTOR
                except Exception:
                    pass
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user {email}'))
            else:
                # update names if provided
                changed = False
                if first and user.first_name != first:
                    user.first_name = first
                    changed = True
                if last and user.last_name != last:
                    user.last_name = last
                    changed = True
                if changed:
                    user.save()

            # create or update instructor profile
            instructor, inst_created = Instructor.objects.get_or_create(user=user, defaults={'employee_no': employee_no, 'title': title})
            if not inst_created:
                instructor.employee_no = employee_no or instructor.employee_no
                instructor.title = title or instructor.title
                instructor.save()

            # generate token
            token = dumps({'user_pk': user.pk}, salt=TOKEN_SALT)
            token_url = f"{options['base_url'].rstrip('/')}/instructor/token-login/{token}/"

            out_rows.append({'email': email, 'token_url': token_url, 'employee_no': employee_no})
            self.stdout.write(self.style.SUCCESS(f'Prepared token for {email}'))

        out_path = Path(options['out'])
        with out_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['email', 'token_url', 'employee_no'])
            writer.writeheader()
            writer.writerows(out_rows)

        self.stdout.write(self.style.SUCCESS(f'Wrote {len(out_rows)} tokens to {out_path}'))
