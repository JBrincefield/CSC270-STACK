from django.core.management.base import BaseCommand, CommandError

from hotdogdelivery.auth_utils import grant_admin_role


class Command(BaseCommand):
    help = 'Grant or remove the Firebase admin custom claim for a user.'

    def add_arguments(self, parser):
        parser.add_argument('uid', help='Firebase Auth user UID')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove the admin claim instead of granting it.',
        )

    def handle(self, *args, **options):
        uid = options['uid']
        try:
            grant_admin_role(uid, enabled=not options['remove'])
        except Exception as exc:  # pragma: no cover - surfaced to CLI
            raise CommandError(f'Failed to update admin role for {uid}: {exc}') from exc

        if options['remove']:
            self.stdout.write(self.style.SUCCESS(f'Removed admin role from {uid}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Granted admin role to {uid}'))
