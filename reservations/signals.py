"""
Signaux Django pour envoyer automatiquement les événements Kafka
lors de la création, modification ou suppression d'indisponibilités
"""
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import Indisponibilites, Indisponibles_tous_temps
from .services.kafka_publisher import get_indisponibilite_publisher
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Indisponibilites)
def indisponibilite_saved(sender, instance, created, **kwargs):
    """
    Publie un événement lors de la création ou mise à jour d'une indisponibilité
    
    Note: Utilise post_save pour s'assurer que l'UUID est généré
    """
    # Éviter la publication lors de la synchronisation depuis Kafka
    # pour éviter les boucles infinies
    if kwargs.get('raw', False):
        # raw=True signifie que c'est un chargement depuis la DB
        return
    
    publisher = get_indisponibilite_publisher()
    try:
        if created:
            publisher.publish_created(instance)
            logger.debug(f"Evenement 'created' publie pour UUID: {instance.uuid}")
        else:
            publisher.publish_updated(instance)
            logger.debug(f"Evenement 'updated' publie pour UUID: {instance.uuid}")
    except Exception as e:
        logger.error(
            f"Erreur lors de la publication de l'evenement: {e}",
            exc_info=True
        )


@receiver(pre_delete, sender=Indisponibilites)
def indisponibilite_deleted(sender, instance, **kwargs):
    """
    Publie un événement lors de la suppression d'une indisponibilité
    
    Note: Utilise pre_delete pour capturer l'UUID avant la suppression
    """
    publisher = get_indisponibilite_publisher()
    try:
        terrain_id = instance.terrain.id if instance.terrain else None
        publisher.publish_deleted(instance.uuid, terrain_id)
        logger.debug(f"Evenement 'deleted' publie pour UUID: {instance.uuid}")
    except Exception as e:
        logger.error(
            f"Erreur lors de la publication de l'evenement de suppression: {e}",
            exc_info=True
        )


# Note: Indisponibles_tous_temps peut utiliser le même publisher si nécessaire
# Pour l'instant, on garde l'ancien système pour cette table
from .services.kafka_service import KafkaService

@receiver(post_save, sender=Indisponibles_tous_temps)
def indisponible_tous_temps_saved(sender, instance, created, **kwargs):
    """
    Envoyer un événement Kafka lorsqu'une indisponibilité tous temps est créée ou modifiée
    """
    if kwargs.get('raw', False):
        return
    
    try:
        action = 'CREATE' if created else 'UPDATE'
        KafkaService.send_indisponible_tous_temps_event(action, instance)
        logger.info(f"Signal post_save: Evenement {action} envoye pour Indisponibles_tous_temps UUID {instance.uuid}")
    except Exception as e:
        logger.error(f"Erreur dans le signal post_save pour Indisponibles_tous_temps: {e}")


@receiver(pre_delete, sender=Indisponibles_tous_temps)
def indisponible_tous_temps_deleted(sender, instance, **kwargs):
    """
    Envoyer un événement Kafka lorsqu'une indisponibilité tous temps est supprimée
    """
    try:
        KafkaService.send_indisponible_tous_temps_event('DELETE', instance)
        logger.info(f"Signal pre_delete: Evenement DELETE envoye pour Indisponibles_tous_temps UUID {instance.uuid}")
    except Exception as e:
        logger.error(f"Erreur dans le signal pre_delete pour Indisponibles_tous_temps: {e}")
