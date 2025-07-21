from django.apps import AppConfig


class SHFAConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shfa'

    def ready(self):
        import apps.shfa.signals  
