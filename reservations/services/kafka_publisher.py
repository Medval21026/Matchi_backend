"""
Service pour publier les événements de synchronisation des horaires indisponibles sur Kafka
"""
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from django.conf import settings
from datetime import date, time
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class IndisponibiliteKafkaPublisher:
    """
    Service pour publier les événements de synchronisation des indisponibilités sur Kafka
    """
    
    def __init__(self):
        self.bootstrap_servers = getattr(
            settings, 
            'KAFKA_BOOTSTRAP_SERVERS', 
            'localhost:9094'
        )
        self.topic = getattr(
            settings, 
            'KAFKA_TOPIC', 
            'horaire-sync-topic'
        )
        self.producer = None
        
    def _get_producer(self):
        """
        Lazy initialization du producer Kafka
        """
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=[self.bootstrap_servers],
                    value_serializer=lambda v: json.dumps(
                        v, 
                        default=self._json_serializer
                    ).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',  # Attendre la confirmation de tous les replicas
                    retries=3,   # Nombre de tentatives en cas d'échec
                    request_timeout_ms=10000,  # Timeout de 10 secondes pour les requêtes (réduit pour éviter les blocages)
                    max_block_ms=5000,  # Timeout de 5 secondes pour bloquer l'envoi (réduit)
                )
                logger.info(
                    f"KafkaProducer initialise - "
                    f"Bootstrap: {self.bootstrap_servers}, "
                    f"Topic: {self.topic}"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de l'initialisation du KafkaProducer: {e}",
                    exc_info=True
                )
                raise
        return self.producer
    
    def _json_serializer(self, obj):
        """
        Sérialiseur personnalisé pour les types Python
        """
        if isinstance(obj, (date, time)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} non serialisable")
    
    @staticmethod
    def calculer_prix(terrain, heure_debut, heure_fin):
        """
        Calcule le prix pour une heure donnée en fonction des périodes tarifaires
        
        Args:
            terrain: Instance de Terrains
            heure_debut: time object
            heure_fin: time object
            
        Returns:
            float: Le prix appliqué
        """
        try:
            from reservations.models import Periode
            
            # Trouver la période tarifaire
            if heure_debut.hour == 23:
                periode = Periode.objects.filter(terrain=terrain).filter(
                    Q(heure_debut__gte=time(23, 0), heure_fin__lte=time(23, 59))
                ).first()
            else:
                periode = Periode.objects.filter(terrain=terrain).filter(
                    Q(heure_debut__lte=heure_debut, heure_fin__gte=heure_fin)
                ).first()
            
            if not periode:
                periode = Periode.objects.filter(terrain=terrain).filter(
                    Q(heure_debut__gte=time(23, 0), heure_fin__lte=time(1, 0)) |
                    Q(heure_debut__gte=time(0, 0), heure_fin__lt=time(5, 0))
                ).first()
            
            prix_applique = float(periode.prix) if periode else float(terrain.prix_par_heure or 0)
            return prix_applique
        except Exception as e:
            logger.warning(f"Erreur lors du calcul du prix: {e}, utilisation du prix par défaut du terrain")
            return float(terrain.prix_par_heure or 0)
    
    def publish_event(self, action, indisponibilite):
        """
        Publie un événement de synchronisation sur Kafka
        
        Args:
            action: "created", "updated", ou "deleted"
            indisponibilite: Instance de Indisponibilites
        """
        try:
            if not indisponibilite.uuid:
                logger.warning(
                    f"Tentative de publication d'un evenement pour une indisponibilite "
                    f"sans UUID: {indisponibilite.id}"
                )
                return
            
            # Récupérer le numéro de téléphone du client via le terrain
            client_num_tel = None
            if indisponibilite.terrain and indisponibilite.terrain.client:
                client_num_tel = indisponibilite.terrain.client.numero_telephone
            
            # Récupérer l'ID et le numéro de téléphone du joueur si présent
            id_jour = None
            joueur_num_tel = None
            if indisponibilite.id_jour:
                id_jour = indisponibilite.id_jour.id
                joueur_num_tel = indisponibilite.id_jour.numero_telephone
            
            # Calculer le prix associé à cette heure
            prix = self.calculer_prix(
                indisponibilite.terrain,
                indisponibilite.heure_debut,
                indisponibilite.heure_fin
            )
            
            event = {
                "uuid": str(indisponibilite.uuid),
                "action": action,
                "terrainId": indisponibilite.terrain.id if indisponibilite.terrain else None,
                "date": [
                    indisponibilite.date_indisponibilite.year,
                    indisponibilite.date_indisponibilite.month,
                    indisponibilite.date_indisponibilite.day
                ] if indisponibilite.date_indisponibilite else None,
                "heureDebut": [
                    indisponibilite.heure_debut.hour,
                    indisponibilite.heure_debut.minute
                ] if indisponibilite.heure_debut else None,
                "heureFin": [
                    indisponibilite.heure_fin.hour,
                    indisponibilite.heure_fin.minute
                ] if indisponibilite.heure_fin else None,
                "typeReservation": None,
                "sourceId": None,
                "description": None,
                "source": "django",
                "numTel": client_num_tel,
                "id_jour": id_jour,
                "joueur_numTel": joueur_num_tel,
                "prix": prix
            }
            
            # Mettre à jour la date de dernière tentative avant l'envoi (si le champ existe)
            try:
                if hasattr(indisponibilite, 'last_kafka_sync_attempt'):
                    indisponibilite.last_kafka_sync_attempt = timezone.now()
                    indisponibilite.save(update_fields=['last_kafka_sync_attempt'])
            except Exception as save_error:
                logger.warning(f"Erreur lors de la mise à jour de last_kafka_sync_attempt: {save_error}")
            
            producer = self._get_producer()
            
            # Utiliser l'UUID comme clé pour garantir l'ordre des messages
            future = producer.send(
                self.topic,
                key=str(indisponibilite.uuid),
                value=event
            )
            
            # Attendre la confirmation (timeout de 10 secondes)
            # Si Kafka ne répond pas, on ne bloque pas l'application
            try:
                record_metadata = future.get(timeout=10)
                # Marquer comme synchronisé seulement si l'envoi réussit (si le champ existe)
                if action != 'deleted' and hasattr(indisponibilite, 'kafka_synced'):
                    try:
                        indisponibilite.kafka_synced = True
                        indisponibilite.save(update_fields=['kafka_synced'])
                    except Exception as save_error:
                        logger.warning(f"Erreur lors de la mise à jour de kafka_synced: {save_error}")
                
                logger.info(
                    f"Evenement publie sur Kafka: action={action}, uuid={indisponibilite.uuid}, "
                    f"topic={record_metadata.topic}, partition={record_metadata.partition}, "
                    f"offset={record_metadata.offset}"
                )
            except KafkaTimeoutError as timeout_error:
                # Marquer comme non synchronisé en cas de timeout (si le champ existe)
                if hasattr(indisponibilite, 'kafka_synced'):
                    try:
                        indisponibilite.kafka_synced = False
                        update_fields = ['kafka_synced']
                        if hasattr(indisponibilite, 'last_kafka_sync_attempt'):
                            update_fields.append('last_kafka_sync_attempt')
                        indisponibilite.save(update_fields=update_fields)
                    except Exception as save_error:
                        logger.warning(f"Erreur lors de la mise à jour du statut de synchronisation: {save_error}")
                
                logger.warning(
                    f"Timeout lors de la publication (Kafka ne répond pas ou est arrêté): {timeout_error}. "
                    f"UUID: {indisponibilite.uuid}, Action: {action}. "
                    f"L'événement sera réessayé automatiquement par le mécanisme de rattrapage."
                )
                # Ne pas lever l'exception pour ne pas bloquer l'application
                # Le mécanisme de rattrapage réessayera plus tard
            
        except KafkaError as e:
            logger.error(f"Erreur Kafka lors de la publication: {e}", exc_info=True)
            # Ne pas lever l'exception pour ne pas bloquer l'application
        except Exception as e:
            logger.error(
                f"Erreur lors de la publication de l'evenement: {e}",
                exc_info=True
            )
    
    def publish_created(self, indisponibilite):
        """
        Publie un événement de création
        """
        self.publish_event("created", indisponibilite)
    
    def publish_updated(self, indisponibilite):
        """
        Publie un événement de mise à jour
        """
        self.publish_event("updated", indisponibilite)
    
    def publish_deleted(self, uuid, terrain_id):
        """
        Publie un événement de suppression
        
        Args:
            uuid: UUID de l'indisponibilité supprimée
            terrain_id: ID du terrain associé
        """
        try:
            # Récupérer le numéro de téléphone du client via le terrain
            client_num_tel = None
            if terrain_id:
                try:
                    from reservations.models import Terrains
                    terrain = Terrains.objects.get(id=terrain_id)
                    if terrain.client:
                        client_num_tel = terrain.client.numero_telephone
                except Terrains.DoesNotExist:
                    logger.warning(f"Terrain {terrain_id} non trouvé lors de la publication de l'événement de suppression")
            
            event = {
                "uuid": str(uuid),
                "action": "deleted",
                "terrainId": terrain_id,
                "date": None,
                "heureDebut": None,
                "heureFin": None,
                "typeReservation": None,
                "sourceId": None,
                "description": None,
                "source": "django",
                "numTel": client_num_tel
            }
            
            producer = self._get_producer()
            future = producer.send(
                self.topic,
                key=str(uuid),
                value=event
            )
            
            # Attendre la confirmation (timeout de 10 secondes)
            try:
                record_metadata = future.get(timeout=10)
                logger.info(
                    f"Evenement de suppression publie: uuid={uuid}, "
                    f"topic={record_metadata.topic}, offset={record_metadata.offset}"
                )
            except KafkaTimeoutError as timeout_error:
                logger.warning(
                    f"Timeout lors de la publication de suppression (Kafka ne répond pas): {timeout_error}. "
                    f"UUID: {uuid}. L'événement sera réessayé automatiquement par le mécanisme de rattrapage."
                )
            
        except KafkaTimeoutError as e:
            logger.error(
                f"Timeout lors de la publication de l'evenement de suppression (Kafka ne répond pas): {e}",
                exc_info=True
            )
            # Ne pas lever l'exception pour ne pas bloquer l'application
        except KafkaError as e:
            logger.error(
                f"Erreur Kafka lors de la publication de l'evenement de suppression: {e}",
                exc_info=True
            )
            # Ne pas lever l'exception pour ne pas bloquer l'application
        except Exception as e:
            logger.error(
                f"Erreur lors de la publication de l'evenement de suppression: {e}",
                exc_info=True
            )
            # Ne pas lever l'exception pour ne pas bloquer l'application
    
    def close(self):
        """
        Ferme le producer Kafka
        """
        if self.producer:
            self.producer.close()
            self.producer = None


# Instance singleton
_indisponibilite_publisher = None


def get_indisponibilite_publisher():
    """
    Retourne l'instance singleton du publisher
    """
    global _indisponibilite_publisher
    if _indisponibilite_publisher is None:
        _indisponibilite_publisher = IndisponibiliteKafkaPublisher()
    return _indisponibilite_publisher
