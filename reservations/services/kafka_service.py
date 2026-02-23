"""
Service Kafka pour envoyer les événements de synchronisation des horaires
"""
import json
import logging
from django.conf import settings
from django.db.models import Q
from datetime import time

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python n'est pas installé. Les événements Kafka ne seront pas envoyés.")


class KafkaService:
    """Service pour envoyer des événements Kafka"""
    
    _producer = None
    
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
    
    @classmethod
    def get_producer(cls):
        """Obtenir ou créer le producteur Kafka"""
        if not KAFKA_AVAILABLE:
            return None
            
        if cls._producer is None:
            try:
                bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')
                cls._producer = KafkaProducer(
                    bootstrap_servers=[bootstrap_servers],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                )
                logger.info(f"Producteur Kafka initialisé avec {bootstrap_servers}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du producteur Kafka: {e}")
                return None
        return cls._producer
    
    @classmethod
    def send_indisponibilite_event(cls, action, indisponibilite):
        """
        Envoyer un événement Kafka pour une indisponibilité
        
        Args:
            action: 'CREATE', 'UPDATE', ou 'DELETE'
            indisponibilite: Instance de Indisponibilites
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka non disponible, événement non envoyé")
            return False
        
        producer = cls.get_producer()
        if producer is None:
            logger.warning("Producteur Kafka non disponible, événement non envoyé")
            return False
        
        try:
            topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
            
            # Préparer le message avec l'UUID
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
            prix = cls.calculer_prix(
                indisponibilite.terrain,
                indisponibilite.heure_debut,
                indisponibilite.heure_fin
            )
            
            message = {
                'action': action,
                'uuid': str(indisponibilite.uuid),
                'terrain_id': indisponibilite.terrain.id,
                'date_indisponibilite': indisponibilite.date_indisponibilite.isoformat(),
                'heure_debut': indisponibilite.heure_debut.isoformat(),
                'heure_fin': indisponibilite.heure_fin.isoformat(),
                'source': 'django',
                'numTel': client_num_tel,
                'id_jour': id_jour,
                'joueur_numTel': joueur_num_tel,
                'prix': prix
            }
            
            # Utiliser l'UUID comme clé pour garantir l'ordre des messages
            producer.send(
                topic,
                key=str(indisponibilite.uuid),
                value=message
            )
            producer.flush()
            
            logger.info(f"Événement Kafka envoyé: {action} pour UUID {indisponibilite.uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'événement Kafka: {e}")
            return False
    
    @classmethod
    def send_indisponible_tous_temps_event(cls, action, indisponible):
        """
        Envoyer un événement Kafka pour une indisponibilité tous temps
        
        Args:
            action: 'CREATE', 'UPDATE', ou 'DELETE'
            indisponible: Instance de Indisponibles_tous_temps
        """
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka non disponible, événement non envoyé")
            return False
        
        producer = cls.get_producer()
        if producer is None:
            logger.warning("Producteur Kafka non disponible, événement non envoyé")
            return False
        
        try:
            topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
            
            # Préparer le message avec l'UUID
            # Récupérer le numéro de téléphone du client via le terrain
            client_num_tel = None
            if indisponible.terrain and indisponible.terrain.client:
                client_num_tel = indisponible.terrain.client.numero_telephone
            
            message = {
                'action': action,
                'uuid': str(indisponible.uuid),
                'terrain_id': indisponible.terrain.id,
                'heure_debut': indisponible.heure_debut.isoformat(),
                'heure_fin': indisponible.heure_fin.isoformat(),
                'type': 'indisponible_tous_temps',
                'source': 'django',
                'numTel': client_num_tel
            }
            
            # Utiliser l'UUID comme clé pour garantir l'ordre des messages
            producer.send(
                topic,
                key=str(indisponible.uuid),
                value=message
            )
            producer.flush()
            
            logger.info(f"Événement Kafka envoyé: {action} pour UUID {indisponible.uuid}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'événement Kafka: {e}")
            return False
    
    @classmethod
    def close(cls):
        """Fermer le producteur Kafka"""
        if cls._producer:
            cls._producer.close()
            cls._producer = None
