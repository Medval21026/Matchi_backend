from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'
    
    def ready(self):
        """Enregistrer les signaux lors du démarrage de l'application"""
        import reservations.signals  # noqa