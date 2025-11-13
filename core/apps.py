from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals
        print("CoreConfig ready. Scheduler should be started via 'manage.py run_scheduler'.")
        pass



