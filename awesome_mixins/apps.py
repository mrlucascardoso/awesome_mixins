from django.apps import AppConfig


class AwesomeMixinsConfig(AppConfig):
    name = 'awesome_mixins'

    def ready(self):
        print('Executado porra')
