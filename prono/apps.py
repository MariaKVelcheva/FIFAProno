from django.apps import AppConfig


class PronoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "prono"

    def ready(self):
        from . import signals  # noqa: F401
