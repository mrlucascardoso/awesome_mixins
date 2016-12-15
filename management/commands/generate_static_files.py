from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'generate static files based in views'

    def handle(self, *args, **options):
        print('Gerando')
