"""
Service Kafka pour envoyer les événements de synchronisation des horaires
"""
import json
import logging
from django.conf import settings
from django.db import models
from django.db.models import Q
from datetime import time
from django.utils import timezone

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaTimeoutError
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
                    request_timeout_ms=10000,  # Timeout de 10 secondes pour les requêtes
                    max_block_ms=5000,  # Timeout de 5 secondes pour bloquer l'envoi
                    retries=0,  # Pas de retry automatique, on gère manuellement
                )
                logger.info(f"Producteur Kafka initialisé avec {bootstrap_servers}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du producteur Kafka: {e}")
                return None
        
        # Note: On ne teste pas la connexion ici car cela peut être lent
        # La connexion sera testée lors du premier send()
        
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
            
            # Mettre à jour la date de dernière tentative avant l'envoi
            indisponibilite.last_kafka_sync_attempt = timezone.now()
            indisponibilite.save(update_fields=['last_kafka_sync_attempt'])
            
            # Utiliser l'UUID comme clé pour garantir l'ordre des messages
            future = producer.send(
                topic,
                key=str(indisponibilite.uuid),
                value=message
            )
            
            # Attendre la confirmation avec un timeout court
            try:
                record_metadata = future.get(timeout=10)
                logger.info(f"Événement Kafka envoyé: {action} pour UUID {indisponibilite.uuid}, topic={record_metadata.topic}, partition={record_metadata.partition}, offset={record_metadata.offset}")
                
                # Marquer comme synchronisé seulement si l'envoi réussit
                if action != 'DELETE':  # Pour DELETE, on ne marque pas comme synced car l'objet sera supprimé
                    indisponibilite.kafka_synced = True
                    indisponibilite.save(update_fields=['kafka_synced'])
                
                return True
            except KafkaTimeoutError as timeout_error:
                logger.error(f"⏱️ Timeout Kafka: Kafka ne répond pas après 10 secondes")
                logger.error(f"   UUID: {indisponibilite.uuid}")
                logger.error(f"   Vérifiez que Kafka est démarré et accessible sur {getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')}")
                # Ne pas marquer comme synchronisé en cas d'erreur
                raise
            except Exception as flush_error:
                logger.error(f"Erreur lors de l'envoi (flush): {flush_error}")
                # Ne pas marquer comme synchronisé en cas d'erreur
                raise
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'événement Kafka: {e}")
            # Marquer comme non synchronisé en cas d'erreur
            try:
                indisponibilite.kafka_synced = False
                indisponibilite.save(update_fields=['kafka_synced', 'last_kafka_sync_attempt'])
            except Exception as save_error:
                logger.error(f"Erreur lors de la mise à jour du statut de synchronisation: {save_error}")
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
            
            # Préparer le message avec l'ID
            # Récupérer le numéro de téléphone du client via le terrain
            client_num_tel = None
            if indisponible.terrain and indisponible.terrain.client:
                client_num_tel = indisponible.terrain.client.numero_telephone
            
            message = {
                'action': action,
                'id': indisponible.id,
                'terrain_id': indisponible.terrain.id,
                'heure_debut': indisponible.heure_debut.isoformat(),
                'heure_fin': indisponible.heure_fin.isoformat(),
                'type': 'indisponible_tous_temps',
                'source': 'django',
                'numTel': client_num_tel
            }
            
            # Utiliser l'ID comme clé pour garantir l'ordre des messages
            producer.send(
                topic,
                key=str(indisponible.id),
                value=message
            )
            producer.flush()
            
            logger.info(f"Événement Kafka envoyé: {action} pour ID {indisponible.id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'événement Kafka: {e}")
            return False
    
    @classmethod
    def sync_unsynced_indisponibilites(cls, max_retries=100, min_interval_minutes=5):
        """
        Synchroniser les indisponibilités non synchronisées avec Kafka (rattrapage)
        IMPORTANT: Ne traite que les indisponibilités qui n'ont JAMAIS été synchronisées avec succès
        
        Args:
            max_retries: Nombre maximum d'indisponibilités à traiter par appel
            min_interval_minutes: Intervalle minimum entre deux tentatives pour la même indisponibilité (en minutes)
        
        Returns:
            dict: Statistiques de synchronisation {'synced': int, 'failed': int, 'skipped': int}
        """
        from reservations.models import Indisponibilites
        from datetime import timedelta
        
        stats = {'synced': 0, 'failed': 0, 'skipped': 0}
        
        if not KAFKA_AVAILABLE:
            logger.warning("Kafka non disponible, synchronisation impossible")
            return stats
        
        producer = cls.get_producer()
        if producer is None:
            logger.error("❌ Producteur Kafka non disponible, synchronisation impossible")
            logger.error("   Vérifiez que:")
            logger.error("   1. Kafka est démarré")
            logger.error("   2. Le port est correct (127.0.0.1:9094)")
            logger.error("   3. Kafka est accessible depuis cette machine")
            return stats
        
        # Calculer la date limite pour éviter de réessayer trop souvent
        min_interval = timezone.now() - timedelta(minutes=min_interval_minutes)
        
        try:
            # Vérifier d'abord si les champs existent (au cas où la migration n'a pas été appliquée)
            try:
                # Test pour voir si le champ existe
                test_query = Indisponibilites.objects.filter(kafka_synced=False)
                test_query.exists()
                fields_exist = True
            except Exception as field_error:
                logger.warning(f"[CATCH-UP] Les champs kafka_synced n'existent pas encore. Migration non appliquée? Erreur: {field_error}")
                logger.warning("[CATCH-UP] Veuillez exécuter: python manage.py migrate reservations")
                fields_exist = False
            
            if not fields_exist:
                return stats
            
            # Synchroniser UNIQUEMENT les indisponibilités qui n'ont JAMAIS été synchronisées avec succès
            # (kafka_synced=False ET qui n'ont pas été tentées récemment)
            unsynced_indisponibilites = Indisponibilites.objects.filter(
                kafka_synced=False  # Seulement celles qui n'ont jamais été synchronisées avec succès
            ).filter(
                models.Q(last_kafka_sync_attempt__isnull=True) | 
                models.Q(last_kafka_sync_attempt__lt=min_interval)
            )[:max_retries]
            
            count = unsynced_indisponibilites.count()
            logger.info(f"[CATCH-UP] Trouvé {count} indisponibilité(s) non synchronisée(s)")
            
            # Log détaillé pour déboguer
            total_indisponibilites = Indisponibilites.objects.count()
            synced_count = Indisponibilites.objects.filter(kafka_synced=True).count()
            unsynced_total = Indisponibilites.objects.filter(kafka_synced=False).count()
            logger.info(f"[CATCH-UP] Statistiques: Total={total_indisponibilites}, Synced={synced_count}, Unsynced={unsynced_total}")
            
            if count == 0:
                logger.info("[CATCH-UP] Aucune indisponibilité à synchroniser (toutes sont déjà synchronisées ou ont été tentées récemment)")
                return stats
            
            for indisponibilite in unsynced_indisponibilites:
                try:
                    # Vérifier à nouveau que l'indisponibilité n'a pas été synchronisée entre-temps
                    # (pour éviter les doublons si plusieurs processus exécutent le rattrapage)
                    indisponibilite.refresh_from_db()
                    if indisponibilite.kafka_synced:
                        logger.debug(f"[CATCH-UP] ⏭️ Indisponibilité {indisponibilite.uuid} déjà synchronisée, ignorée")
                        stats['skipped'] += 1
                        continue
                    
                    logger.info(f"[CATCH-UP] Tentative de synchronisation: UUID={indisponibilite.uuid}, Terrain={indisponibilite.terrain.id}, Date={indisponibilite.date_indisponibilite}")
                    
                    # Envoyer l'événement CREATE
                    # send_indisponibilite_event met automatiquement à jour kafka_synced=True si succès
                    success = cls.send_indisponibilite_event('CREATE', indisponibilite)
                    
                    # Vérifier à nouveau après l'envoi
                    indisponibilite.refresh_from_db()
                    
                    if success and indisponibilite.kafka_synced:
                        stats['synced'] += 1
                        logger.info(f"[CATCH-UP] ✅ Indisponibilité {indisponibilite.uuid} synchronisée avec succès")
                    else:
                        stats['failed'] += 1
                        logger.warning(f"[CATCH-UP] ❌ Échec de synchronisation pour {indisponibilite.uuid} (success={success}, kafka_synced={indisponibilite.kafka_synced})")
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"[CATCH-UP] Erreur lors de la synchronisation de {indisponibilite.uuid}: {e}", exc_info=True)
            
            logger.info(f"[CATCH-UP] Synchronisation terminée: {stats['synced']} synchronisées, {stats['failed']} échecs, {stats['skipped']} ignorées")
            
        except Exception as e:
            logger.error(f"[CATCH-UP] Erreur lors du rattrapage: {e}", exc_info=True)
        
        return stats
    
    @classmethod
    def close(cls):
        """Fermer le producteur Kafka"""
        if cls._producer:
            cls._producer.close()
            cls._producer = None
