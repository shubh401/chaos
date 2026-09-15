from django.apps import AppConfig


class IsolatedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'isolated'
