"""
Consumer Kafka pour écouter les événements de synchronisation des horaires
"""
import json
import logging
import threading
import time
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python n'est pas installé. Le consumer Kafka ne peut pas fonctionner.")


class KafkaConsumerService:
    """Service pour consommer les événements Kafka"""
    
    _consumer = None
    _thread = None
    _running = False
    
    @classmethod
    def get_consumer(cls):
        """Obtenir ou créer le consumer Kafka"""
        if not KAFKA_AVAILABLE:
            return None
            
        if cls._consumer is None:
            try:
                bootstrap_servers_str = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')
                topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
                
                # Convertir la chaîne en liste si nécessaire
                if isinstance(bootstrap_servers_str, str):
                    bootstrap_servers = [bootstrap_servers_str]
                else:
                    bootstrap_servers = bootstrap_servers_str
                
                logger.info(f"Tentative de connexion à Kafka sur {bootstrap_servers}...")
                
                # Créer le consumer avec configuration optimale
                def safe_value_deserializer(m):
                    """Deserializer sécurisé qui gère les valeurs None"""
                    if m is None:
                        return None
                    try:
                        return json.loads(m.decode('utf-8'))
                    except Exception as e:
                        logger.warning(f"Erreur de deserialization: {e}")
                        return None
                
                def safe_key_deserializer(k):
                    """Deserializer de clé sécurisé"""
                    if k is None:
                        return None
                    try:
                        return k.decode('utf-8')
                    except:
                        return None
                
                cls._consumer = KafkaConsumer(
                    bootstrap_servers=bootstrap_servers,
                    group_id='django-reservation-consumer-group',
                    value_deserializer=safe_value_deserializer,
                    key_deserializer=safe_key_deserializer,
                    auto_offset_reset='earliest',  # Lire depuis le début pour consommer les messages en attente
                    enable_auto_commit=False,  # Commit manuel pour plus de contrôle
                    consumer_timeout_ms=2000,
                    request_timeout_ms=40000,  # Doit être > session_timeout_ms
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,  # Heartbeat toutes les 10 secondes pour rester actif
                    max_poll_records=50,  # Augmenter le batch pour traiter plus rapidement les 410 messages en attente
                    max_poll_interval_ms=300000,  # 5 minutes max entre polls
                )
                
                logger.info("Connexion au broker Kafka...")
                
                # S'abonner au topic (cela force la connexion)
                logger.info(f"Abonnement au topic: {topic}")
                try:
                    cls._consumer.subscribe([topic])
                    logger.info("✅ Abonné au topic")
                except Exception as sub_error:
                    logger.error(f"❌ Erreur lors de l'abonnement au topic: {sub_error}")
                    logger.error(f"Vérifiez que Kafka est démarré sur {bootstrap_servers}")
                    try:
                        cls._consumer.close()
                    except:
                        pass
                    cls._consumer = None
                    return None
                
                # Forcer la connexion en faisant un poll (c'est plus fiable que bootstrap_connected())
                # Kafka crée le consumer group et établit la connexion lors du premier poll
                logger.info("Test de connexion (premier poll)...")
                max_retries = 3
                connected = False
                for retry in range(max_retries):
                    try:
                        # Faire un poll pour forcer la connexion
                        message_pack = cls._consumer.poll(timeout_ms=2000)
                        # Si on arrive ici sans exception, la connexion fonctionne
                        connected = True
                        if message_pack:
                            logger.info(f"✅ Connecté - Messages reçus lors de l'initialisation: {len(message_pack)} partitions")
                        else:
                            logger.info("✅ Connecté au broker Kafka (aucun message disponible)")
                        break
                    except Exception as poll_error:
                        if retry < max_retries - 1:
                            logger.warning(f"⚠️ Tentative de connexion {retry + 1}/{max_retries}... (erreur: {poll_error})")
                            time.sleep(1)
                        else:
                            logger.error(f"❌ Impossible de se connecter au broker Kafka après {max_retries} tentatives")
                            logger.error(f"Erreur: {poll_error}")
                            logger.error(f"Vérifiez que Kafka est démarré sur {bootstrap_servers}")
                            try:
                                cls._consumer.close()
                            except:
                                pass
                            cls._consumer = None
                            return None
                
                if not connected:
                    logger.error("❌ Impossible de se connecter au broker Kafka")
                    logger.error(f"Vérifiez que Kafka est démarré sur {bootstrap_servers}")
                    try:
                        cls._consumer.close()
                    except:
                        pass
                    cls._consumer = None
                    return None
                
                # Récupérer les partitions assignées (force l'enregistrement)
                # Attendre plus longtemps pour l'assignation des partitions (jusqu'à 5 secondes)
                max_wait = 5
                waited = 0
                partitions = set()
                while waited < max_wait and not partitions:
                    time.sleep(0.5)
                    waited += 0.5
                    try:
                        partitions = cls._consumer.assignment()
                        if partitions:
                            break
                    except:
                        pass
                
                try:
                    if partitions:
                        logger.info(f"✅ Partitions assignées: {partitions}")
                        
                        # Si des partitions sont assignées, vérifier les offsets
                        for partition in partitions:
                            try:
                                # Obtenir les offsets earliest et latest
                                earliest = cls._consumer.beginning_offsets([partition])[partition]
                                latest = cls._consumer.end_offsets([partition])[partition]
                                
                                # Obtenir l'offset actuel (committed ou position)
                                try:
                                    committed = cls._consumer.committed(partition)
                                    if committed is not None:
                                        current = committed
                                    else:
                                        current = cls._consumer.position(partition)
                                except:
                                    current = earliest
                                
                                logger.info(f"  Partition {partition.partition}: earliest={earliest}, current={current}, latest={latest}")
                                
                                # Si l'offset actuel est à la fin ou None, se repositionner au début
                                if current is None or (current >= latest and earliest < latest):
                                    logger.warning(f"  ⚠️ Offset a la fin ou None, repositionnement au debut...")
                                    cls._consumer.seek(partition, earliest)
                                    logger.info(f"  ✅ Repositionne a l'offset {earliest}")
                                elif current < earliest:
                                    # Si l'offset est avant le début (impossible), se repositionner au début
                                    logger.warning(f"  ⚠️ Offset invalide ({current} < {earliest}), repositionnement...")
                                    cls._consumer.seek(partition, earliest)
                                    logger.info(f"  ✅ Repositionne a l'offset {earliest}")
                            except Exception as e:
                                logger.warning(f"  ⚠️ Impossible de verifier l'offset pour partition {partition}: {e}")
                    else:
                        logger.warning(f"⚠️ Aucune partition assignee apres {max_wait}s, le consumer group pourrait etre vide ou il y a plusieurs instances")
                        logger.warning("   Verifiez dans Kafka UI qu'il n'y a qu'une seule instance du consumer")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible de récupérer les partitions: {e}")
                
                logger.info("=" * 60)
                logger.info("✅ CONSUMER KAFKA INITIALISÉ AVEC SUCCÈS")
                logger.info(f"   Topic: {topic}")
                logger.info(f"   Consumer Group ID: django-reservation-consumer-group")
                logger.info(f"   Bootstrap Servers: {bootstrap_servers}")
                logger.info("=" * 60)
                logger.info("ℹ️  Le consumer group devrait apparaître dans Kafka UI maintenant")
                logger.info("ℹ️  Si le group n'apparaît pas, attendez quelques secondes ou")
                logger.info("   consommez un message pour forcer la création")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du consumer Kafka: {e}")
                logger.error(f"Détails: type={type(e).__name__}, message={str(e)}")
                logger.error(f"Vérifiez que Kafka est démarré et accessible sur {bootstrap_servers}")
                if cls._consumer:
                    try:
                        cls._consumer.close()
                    except:
                        pass
                    cls._consumer = None
                return None
        return cls._consumer
    
    @classmethod
    def process_message(cls, message):
        """
        Traiter un message reçu de Kafka et synchroniser avec Django
        
        Args:
            message: Message Kafka avec value et key
        """
        try:
            # Importer ici pour éviter les imports circulaires
            from django.db import transaction
            from django.db.models.signals import post_save, post_delete
            from reservations.models import Indisponibilites, Indisponibles_tous_temps, Terrains, Client
            from reservations.signals import (
                indisponibilite_saved, indisponibilite_deleted,
                indisponible_tous_temps_saved, indisponible_tous_temps_deleted
            )
            from datetime import datetime, date, time
            import uuid as uuid_lib
            
            # Vérifier que le message a une valeur
            data = message.value
            if data is None:
                logger.warning(f"[ERREUR] Message avec value=None ignoré (offset: {message.offset}, partition: {message.partition})")
                return
            
            action = data.get('action', '').lower()  # Utiliser lowercase pour correspondre à Spring Boot
            uuid_str = data.get('uuid')
            source = data.get('source', 'unknown')
            
            logger.info(f"[MESSAGE] Offset: {message.offset}, Partition: {message.partition}")
            logger.info(f"[MESSAGE] Action: {action}, UUID: {uuid_str}, Source: {source}")
            logger.info(f"[MESSAGE] Donnees completes: {json.dumps(data, indent=2, default=str)}")
            
            # Si le message vient de Django, on ne le traite pas (éviter les boucles)
            # MAIS on doit quand même avancer dans le topic pour réduire le lag
            if source == 'django':
                logger.info(f"[IGNORE] Message ignore car source=django (evite la boucle) - UUID: {uuid_str}, Offset: {message.offset}, Partition: {message.partition}")
                # On retourne sans traiter, mais le commit sera fait après dans la boucle principale
                # pour avancer dans le topic et réduire le lag
                return
            
            # Si source n'est pas 'django', c'est un message de Spring Boot - on doit le traiter
            logger.info(f"[TRAITEMENT] Message de Spring Boot detecte (source={source}), traitement...")
            
            if not uuid_str:
                logger.warning("Message ignoré: UUID manquant")
                return
            
            try:
                message_uuid = uuid_lib.UUID(uuid_str)
            except ValueError:
                logger.error(f"UUID invalide: {uuid_str}")
                return
            
            # Désactiver temporairement les signaux pour éviter une boucle infinie
            post_save.disconnect(indisponibilite_saved, sender=Indisponibilites)
            post_save.disconnect(indisponible_tous_temps_saved, sender=Indisponibles_tous_temps)
            post_delete.disconnect(indisponibilite_deleted, sender=Indisponibilites)
            post_delete.disconnect(indisponible_tous_temps_deleted, sender=Indisponibles_tous_temps)
            
            # Vérifier les données AVANT d'entrer dans la transaction
            # Déterminer le type d'indisponibilité
            type_indisponible = data.get('type') or data.get('typeReservation')
            
            # Utiliser proprietaireTelephone pour trouver le terrain
            proprietaire_telephone = data.get('proprietaireTelephone') or data.get('proprietaire_telephone')
            terrain_id_spring = data.get('terrainId') or data.get('terrain_id')
            
            if not proprietaire_telephone:
                logger.warning(f"[ERREUR] Message ignoré: proprietaireTelephone manquant pour UUID {uuid_str}")
                logger.warning(f"  Données reçues: {json.dumps(data, indent=2, default=str)}")
                logger.warning(f"  Offset: {message.offset}, Partition: {message.partition}")
                return
            
            # Convertir en int si c'est une string
            try:
                if isinstance(proprietaire_telephone, str):
                    proprietaire_telephone = int(proprietaire_telephone)
            except (ValueError, TypeError):
                logger.error(f"[ERREUR] proprietaireTelephone invalide: {proprietaire_telephone} (type: {type(proprietaire_telephone)})")
                logger.error(f"  Offset: {message.offset}, Partition: {message.partition}")
                return
            
            # Trouver le client (propriétaire) par son numéro de téléphone
            try:
                client = Client.objects.get(numero_telephone=proprietaire_telephone)
                logger.info(f"[CLIENT] Client trouvé: ID={client.id}, Téléphone={client.numero_telephone}")
            except Client.DoesNotExist:
                logger.error(f"[ERREUR] Client avec téléphone {proprietaire_telephone} n'existe pas pour UUID {uuid_str}")
                logger.error(f"  Offset: {message.offset}, Partition: {message.partition}")
                return
            except Client.MultipleObjectsReturned:
                logger.warning(f"[WARNING] Plusieurs clients avec téléphone {proprietaire_telephone}, utilisation du premier")
                client = Client.objects.filter(numero_telephone=proprietaire_telephone).first()
            
            # Trouver le terrain du client
            terrains = Terrains.objects.filter(client=client)
            
            if not terrains.exists():
                logger.error(f"[ERREUR] Aucun terrain trouvé pour le client {client.id} (téléphone: {proprietaire_telephone}) - UUID {uuid_str}")
                logger.error(f"  Offset: {message.offset}, Partition: {message.partition}")
                return
            
            # Si plusieurs terrains, utiliser le premier ou celui avec l'ID correspondant si possible
            if terrains.count() == 1:
                terrain = terrains.first()
                logger.info(f"[TERRAIN] Terrain unique trouvé: ID={terrain.id}, Nom={terrain.nom_fr}")
            else:
                # Plusieurs terrains : essayer de trouver celui avec l'ID Spring Boot si fourni
                if terrain_id_spring:
                    terrain = terrains.filter(id=terrain_id_spring).first()
                    if terrain:
                        logger.info(f"[TERRAIN] Terrain trouvé par ID Spring Boot: ID={terrain.id}, Nom={terrain.nom_fr}")
                    else:
                        # Si l'ID Spring Boot ne correspond à aucun terrain, utiliser le premier
                        terrain = terrains.first()
                        logger.warning(f"[WARNING] Terrain ID {terrain_id_spring} (Spring Boot) non trouvé, utilisation du premier terrain du client: ID={terrain.id}")
                else:
                    # Pas d'ID Spring Boot, utiliser le premier terrain
                    terrain = terrains.first()
                    logger.info(f"[TERRAIN] Plusieurs terrains trouvés, utilisation du premier: ID={terrain.id}, Nom={terrain.nom_fr}")
            
            # Maintenant entrer dans la transaction pour traiter le message
            try:
                with transaction.atomic():
                    # Traiter selon le type
                    if type_indisponible == 'indisponible_tous_temps':
                        cls._process_indisponible_tous_temps(
                            action, message_uuid, terrain, data
                        )
                    else:
                        # Indisponibilité normale
                        cls._process_indisponibilite(
                            action, message_uuid, terrain, data
                        )
                    
                    logger.info(f"✅ Message traité avec succès: {action} pour UUID {uuid_str}")
                    
            finally:
                # Réactiver les signaux
                post_save.connect(indisponibilite_saved, sender=Indisponibilites)
                post_save.connect(indisponible_tous_temps_saved, sender=Indisponibles_tous_temps)
                post_delete.connect(indisponibilite_deleted, sender=Indisponibilites)
                post_delete.connect(indisponible_tous_temps_deleted, sender=Indisponibles_tous_temps)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}", exc_info=True)
    
    @classmethod
    def _process_indisponibilite(cls, action, message_uuid, terrain, data):
        """Traiter une indisponibilité normale"""
        from reservations.models import Indisponibilites
        from datetime import datetime, date, time
        
        if action == 'delete' or action == 'deleted':
            # Supprimer l'indisponibilité
            # Essayer d'abord par UUID
            try:
                indisponibilite = Indisponibilites.objects.get(uuid=message_uuid)
                indisponibilite.delete()
                logger.info(f"[DELETE] Indisponibilite supprimee par UUID: {message_uuid}")
                return
            except Indisponibilites.DoesNotExist:
                logger.warning(f"[DELETE] Indisponibilite non trouvee par UUID: {message_uuid}, recherche par criteres...")
            except Exception as e:
                logger.warning(f"[DELETE] Erreur lors de la recherche par UUID: {e}, recherche par criteres...")
            
            # Si pas trouvé par UUID, essayer de trouver par terrain, date et heures
            # (utile pour les abonnements où plusieurs UUID peuvent correspondre)
            try:
                date_data = data.get('date') or data.get('date_indisponibilite')
                heure_debut_data = data.get('heureDebut') or data.get('heure_debut')
                heure_fin_data = data.get('heureFin') or data.get('heure_fin')
                
                logger.info(f"[DELETE] Recherche par criteres: date={date_data}, heure_debut={heure_debut_data}, heure_fin={heure_fin_data}, terrain={terrain.id}")
                
                if date_data and heure_debut_data and heure_fin_data:
                    # Parser la date
                    try:
                        if isinstance(date_data, list):
                            date_indisponibilite = date(date_data[0], date_data[1], date_data[2])
                        elif isinstance(date_data, str):
                            if 'T' in date_data:
                                date_indisponibilite = datetime.fromisoformat(date_data.replace('Z', '+00:00')).date()
                            else:
                                date_indisponibilite = datetime.strptime(date_data, '%Y-%m-%d').date()
                        else:
                            date_indisponibilite = None
                    except Exception as e:
                        logger.error(f"[DELETE] Erreur lors du parsing de la date: {e}")
                        date_indisponibilite = None
                    
                    # Parser les heures avec gestion spéciale pour 23h -> 0h
                    heure_debut = None
                    heure_fin = None
                    
                    if date_indisponibilite:
                        try:
                            if isinstance(heure_debut_data, list):
                                heure_val = heure_debut_data[0]
                                minute_val = heure_debut_data[1] if len(heure_debut_data) > 1 else 0
                                if 0 <= heure_val <= 23:
                                    heure_debut = time(heure_val, minute_val)
                                else:
                                    logger.error(f"[DELETE] Heure debut invalide: {heure_val}")
                            elif isinstance(heure_debut_data, str):
                                if len(heure_debut_data.split(':')) == 2:
                                    heure_debut = datetime.strptime(heure_debut_data, '%H:%M').time()
                                else:
                                    heure_debut = datetime.strptime(heure_debut_data, '%H:%M:%S').time()
                        except Exception as e:
                            logger.error(f"[DELETE] Erreur lors du parsing de l'heure debut: {e}")
                        
                        try:
                            if isinstance(heure_fin_data, list):
                                heure_val = heure_fin_data[0]
                                minute_val = heure_fin_data[1] if len(heure_fin_data) > 1 else 0
                                if 0 <= heure_val <= 23:
                                    heure_fin = time(heure_val, minute_val)
                                else:
                                    logger.error(f"[DELETE] Heure fin invalide: {heure_val}")
                            elif isinstance(heure_fin_data, str):
                                if len(heure_fin_data.split(':')) == 2:
                                    heure_fin = datetime.strptime(heure_fin_data, '%H:%M').time()
                                else:
                                    heure_fin = datetime.strptime(heure_fin_data, '%H:%M:%S').time()
                        except Exception as e:
                            logger.error(f"[DELETE] Erreur lors du parsing de l'heure fin: {e}")
                        
                        if heure_debut and heure_fin:
                            logger.info(f"[DELETE] Recherche avec: terrain={terrain.id}, date={date_indisponibilite}, heure_debut={heure_debut}, heure_fin={heure_fin}")
                            
                            # Chercher toutes les indisponibilités correspondantes
                            # Pour les abonnements, on cherche exactement par terrain, date, heure_debut, heure_fin
                            indisponibilites = Indisponibilites.objects.filter(
                                terrain=terrain,
                                date_indisponibilite=date_indisponibilite,
                                heure_debut=heure_debut,
                                heure_fin=heure_fin,
                                id_jour__isnull=True  # Uniquement celles venant de Spring Boot
                            )
                            
                            count = indisponibilites.count()
                            logger.info(f"[DELETE] Trouve {count} indisponibilite(s) correspondante(s)")
                            
                            if count > 0:
                                # Supprimer toutes les indisponibilités trouvées
                                deleted_count = 0
                                for ind in indisponibilites:
                                    try:
                                        ind.delete()
                                        deleted_count += 1
                                    except Exception as e:
                                        logger.error(f"[DELETE] Erreur lors de la suppression de l'indisponibilite {ind.id}: {e}")
                                
                                logger.info(f"[DELETE] {deleted_count}/{count} indisponibilite(s) supprimee(s) par criteres: terrain={terrain.id}, date={date_indisponibilite}, heure_debut={heure_debut}, heure_fin={heure_fin}")
                                return
                            else:
                                # Si aucune trouvée avec les critères exacts, essayer sans la contrainte id_jour
                                indisponibilites = Indisponibilites.objects.filter(
                                    terrain=terrain,
                                    date_indisponibilite=date_indisponibilite,
                                    heure_debut=heure_debut,
                                    heure_fin=heure_fin
                                )
                                count = indisponibilites.count()
                                if count > 0:
                                    deleted_count = 0
                                    for ind in indisponibilites:
                                        try:
                                            ind.delete()
                                            deleted_count += 1
                                        except Exception as e:
                                            logger.error(f"[DELETE] Erreur lors de la suppression de l'indisponibilite {ind.id}: {e}")
                                    logger.info(f"[DELETE] {deleted_count}/{count} indisponibilite(s) supprimee(s) (sans filtre id_jour): terrain={terrain.id}, date={date_indisponibilite}, heure_debut={heure_debut}, heure_fin={heure_fin}")
                                    return
                                else:
                                    logger.warning(f"[DELETE] Aucune indisponibilite trouvee avec les criteres: terrain={terrain.id}, date={date_indisponibilite}, heure_debut={heure_debut}, heure_fin={heure_fin}")
                        else:
                            logger.warning(f"[DELETE] Impossible de parser les heures: heure_debut={heure_debut}, heure_fin={heure_fin}")
                    else:
                        logger.warning(f"[DELETE] Impossible de parser la date: {date_data}")
                else:
                    logger.warning(f"[DELETE] Donnees incompletes pour la recherche par criteres: date={date_data}, heure_debut={heure_debut_data}, heure_fin={heure_fin_data}")
            except Exception as e:
                logger.error(f"[DELETE] Erreur lors de la recherche par criteres: {e}", exc_info=True)
            
            logger.warning(f"[DELETE] Impossible de supprimer l'indisponibilite: UUID {message_uuid}")
            return
        
        # Parser les dates et heures depuis Spring Boot
        # Spring Boot utilise 'date', Django utilise 'date_indisponibilite'
        date_data = data.get('date') or data.get('date_indisponibilite')
        # Spring Boot utilise 'heureDebut'/'heureFin', Django utilise 'heure_debut'/'heure_fin'
        heure_debut_data = data.get('heureDebut') or data.get('heure_debut')
        heure_fin_data = data.get('heureFin') or data.get('heure_fin')
        
        logger.info(f"[PARSING] date_data: {date_data}, heure_debut: {heure_debut_data}, heure_fin: {heure_fin_data}")
        
        if not all([date_data, heure_debut_data, heure_fin_data]):
            logger.warning(f"[ERREUR] Donnees incompletes pour UUID {message_uuid}")
            logger.warning(f"  date_data: {date_data}")
            logger.warning(f"  heure_debut_data: {heure_debut_data}")
            logger.warning(f"  heure_fin_data: {heure_fin_data}")
            return
        
        # Convertir la date [2026, 1, 20] (format Spring Boot) ou string ISO
        try:
            if isinstance(date_data, list):
                # Format Spring Boot: [2026, 1, 20]
                date_indisponibilite = date(date_data[0], date_data[1], date_data[2])
                logger.info(f"[PARSING] Date parsee depuis liste: {date_indisponibilite}")
            elif isinstance(date_data, str):
                # Format ISO string: "2026-01-20"
                if 'T' in date_data:
                    date_indisponibilite = datetime.fromisoformat(date_data.replace('Z', '+00:00')).date()
                else:
                    date_indisponibilite = datetime.strptime(date_data, '%Y-%m-%d').date()
                logger.info(f"[PARSING] Date parsee depuis string: {date_indisponibilite}")
            else:
                logger.error(f"[ERREUR] Format de date inconnu: {type(date_data)} - {date_data}")
                return
        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du parsing de la date: {e}, date_data: {date_data}")
            return
        
        # Convertir les heures [18, 0] (format Spring Boot) ou string ISO
        try:
            if isinstance(heure_debut_data, list):
                # Format Spring Boot: [18, 0] ou [18, 0, 0] ou [23, 0]
                # Gérer correctement l'heure 23h
                heure_val = heure_debut_data[0]
                minute_val = heure_debut_data[1] if len(heure_debut_data) > 1 else 0
                # S'assurer que l'heure est valide (0-23)
                if heure_val < 0 or heure_val > 23:
                    logger.error(f"[ERREUR] Heure debut invalide: {heure_val} (doit être entre 0 et 23)")
                    return
                heure_debut = time(heure_val, minute_val)
                logger.info(f"[PARSING] Heure debut parsee depuis liste: {heure_debut} (valeur brute: {heure_debut_data})")
            elif isinstance(heure_debut_data, str):
                # Format ISO string: "18:00:00" ou "18:00" ou "23:00"
                if len(heure_debut_data.split(':')) == 2:
                    heure_debut = datetime.strptime(heure_debut_data, '%H:%M').time()
                else:
                    heure_debut = datetime.strptime(heure_debut_data, '%H:%M:%S').time()
                logger.info(f"[PARSING] Heure debut parsee depuis string: {heure_debut}")
            else:
                logger.error(f"[ERREUR] Format d'heure debut inconnu: {type(heure_debut_data)} - {heure_debut_data}")
                return
        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du parsing de l'heure debut: {e}, heure_debut_data: {heure_debut_data}")
            return
        
        try:
            if isinstance(heure_fin_data, list):
                # Format Spring Boot: [19, 0] ou [19, 0, 0] ou [0, 0] pour minuit
                # Gérer correctement l'heure 0h (minuit) qui peut être l'heure de fin pour 23h
                heure_val = heure_fin_data[0]
                minute_val = heure_fin_data[1] if len(heure_fin_data) > 1 else 0
                # S'assurer que l'heure est valide (0-23)
                if heure_val < 0 or heure_val > 23:
                    logger.error(f"[ERREUR] Heure fin invalide: {heure_val} (doit être entre 0 et 23)")
                    return
                heure_fin = time(heure_val, minute_val)
                logger.info(f"[PARSING] Heure fin parsee depuis liste: {heure_fin} (valeur brute: {heure_fin_data})")
            elif isinstance(heure_fin_data, str):
                # Format ISO string: "19:00:00" ou "19:00" ou "00:00" pour minuit
                if len(heure_fin_data.split(':')) == 2:
                    heure_fin = datetime.strptime(heure_fin_data, '%H:%M').time()
                else:
                    heure_fin = datetime.strptime(heure_fin_data, '%H:%M:%S').time()
                logger.info(f"[PARSING] Heure fin parsee depuis string: {heure_fin}")
            else:
                logger.error(f"[ERREUR] Format d'heure fin inconnu: {type(heure_fin_data)} - {heure_fin_data}")
                return
        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors du parsing de l'heure fin: {e}, heure_fin_data: {heure_fin_data}")
            return
        
        # CREATE ou UPDATE
        try:
            logger.info(f"[SAUVEGARDE] Creation/mise a jour de l'indisponibilite...")
            logger.info(f"  UUID: {message_uuid}")
            logger.info(f"  Terrain ID: {terrain.id}")
            logger.info(f"  Date (Spring 'date' -> Django 'date_indisponibilite'): {date_indisponibilite}")
            logger.info(f"  Heure debut (Spring 'heureDebut' -> Django 'heure_debut'): {heure_debut}")
            logger.info(f"  Heure fin (Spring 'heureFin' -> Django 'heure_fin'): {heure_fin}")
            
            # Pour tous les événements venant de Spring Boot, id_jour est toujours null
            defaults_data = {
                'terrain': terrain,
                'date_indisponibilite': date_indisponibilite,
                'heure_debut': heure_debut,
                'heure_fin': heure_fin,
                'id_jour': None
            }
            
            # Vérifier d'abord l'existence pour éviter les erreurs d'intégrité
            # 1. Chercher par UUID
            indisponibilite = Indisponibilites.objects.filter(uuid=message_uuid).first()
            
            if indisponibilite:
                # Mettre à jour l'existante trouvée par UUID
                for key, value in defaults_data.items():
                    setattr(indisponibilite, key, value)
                indisponibilite.save()
                created = False
                logger.info(f"[UPDATE] Indisponibilite mise a jour par UUID: {message_uuid}")
            else:
                # 2. Chercher par critères (terrain, date, heures) - pour les abonnements
                existing = Indisponibilites.objects.filter(
                    terrain=terrain,
                    date_indisponibilite=date_indisponibilite,
                    heure_debut=heure_debut,
                    heure_fin=heure_fin,
                    id_jour__isnull=True
                ).first()
                
                if existing:
                    # Mettre à jour l'existante avec le nouvel UUID
                    existing.uuid = message_uuid
                    existing.save()
                    indisponibilite = existing
                    created = False
                    logger.info(f"[UPDATE] Indisponibilite existante mise a jour avec nouvel UUID: {message_uuid}")
                else:
                    # 3. Créer une nouvelle indisponibilité
                    defaults_data['uuid'] = message_uuid
                    indisponibilite = Indisponibilites.objects.create(**defaults_data)
                    created = True
                    logger.info(f"[CREATE] Nouvelle indisponibilite creee: UUID {message_uuid}")
            
            action_text = "creee" if created else "mise a jour"
            logger.info(f"[SUCCES] Indisponibilite {action_text} dans Django: UUID {message_uuid}")
            logger.info(f"[SUCCES] ID Django: {indisponibilite.id}, Terrain: {terrain.id}, Date: {date_indisponibilite}")
        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la creation/mise a jour: {e}", exc_info=True)
            # En cas d'erreur, vérifier si l'indisponibilité existe déjà
            from django.db import IntegrityError
            if isinstance(e, IntegrityError) or 'Duplicate entry' in str(e) or 'unique constraint' in str(e).lower():
                logger.warning(f"[WARNING] Contrainte unique violee, recherche de l'indisponibilite existante...")
                existing = Indisponibilites.objects.filter(
                    terrain=terrain,
                    date_indisponibilite=date_indisponibilite,
                    heure_debut=heure_debut,
                    heure_fin=heure_fin,
                    id_jour__isnull=True
                ).first()
                if existing:
                    logger.info(f"[INFO] Indisponibilite deja existante trouvee (ID: {existing.id}), message ignore")
                    return
            raise
    
    @classmethod
    def _process_indisponible_tous_temps(cls, action, message_uuid, terrain, data):
        """Traiter une indisponibilité tous temps"""
        from reservations.models import Indisponibles_tous_temps
        from datetime import datetime, time
        
        if action == 'DELETE' or action == 'DELETED':
            try:
                indisponible = Indisponibles_tous_temps.objects.get(uuid=message_uuid)
                indisponible.delete()
                logger.info(f"Indisponible tous temps supprimée: UUID {message_uuid}")
            except Indisponibles_tous_temps.DoesNotExist:
                logger.warning(f"Indisponible tous temps non trouvée: UUID {message_uuid}")
            return
        
        # Parser les heures
        heure_debut_data = data.get('heureDebut') or data.get('heure_debut')
        heure_fin_data = data.get('heureFin') or data.get('heure_fin')
        
        if not all([heure_debut_data, heure_fin_data]):
            logger.warning(f"Données incomplètes pour UUID {message_uuid}")
            return
        
        if isinstance(heure_debut_data, list):
            heure_debut = time(heure_debut_data[0], heure_debut_data[1])
        else:
            heure_debut = datetime.fromisoformat(heure_debut_data.replace('Z', '+00:00')).time()
        
        if isinstance(heure_fin_data, list):
            heure_fin = time(heure_fin_data[0], heure_fin_data[1])
        else:
            heure_fin = datetime.fromisoformat(heure_fin_data.replace('Z', '+00:00')).time()
        
        # CREATE ou UPDATE
        indisponible, created = Indisponibles_tous_temps.objects.update_or_create(
            uuid=message_uuid,
            defaults={
                'terrain': terrain,
                'heure_debut': heure_debut,
                'heure_fin': heure_fin,
            }
        )
        
        action_text = "créée" if created else "mise à jour"
        logger.info(f"Indisponible tous temps {action_text}: UUID {message_uuid}")
    
    @classmethod
    def start_consuming(cls):
        """Démarrer la consommation des messages Kafka"""
        if cls._running:
            logger.warning("⚠️ Le consumer Kafka est déjà en cours d'exécution")
            logger.warning("⚠️ Arrêt de l'instance précédente...")
            cls.stop_consuming()
            # Attendre un peu pour que l'arrêt se termine
            time.sleep(2)
        
        # Fermer le consumer existant s'il existe
        if cls._consumer is not None:
            try:
                cls._consumer.close()
                logger.info("✅ Ancien consumer ferme")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de la fermeture de l'ancien consumer: {e}")
            cls._consumer = None
        
        # Attendre un peu pour que Kafka libère les ressources
        time.sleep(1)
        
        consumer = cls.get_consumer()
        if consumer is None:
            logger.error("❌ Impossible de démarrer le consumer: consumer non disponible")
            logger.error("La connexion a été testée dans get_consumer() via un poll")
            return False
        
        # La connexion a déjà été testée dans get_consumer() via un poll
        # Si on arrive ici, le consumer est connecté et prêt
        logger.info("✅ Consumer connecté et prêt à consommer")
        
        cls._running = True
        message_count = 0
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("CONSUMER KAFKA DEMARRE")
        logger.info("=" * 60)
        logger.info(f"Topic: {getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')}")
        logger.info(f"Group ID: django-reservation-consumer-group")
        logger.info(f"Bootstrap Servers: {getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')}")
        logger.info("")
        logger.info("Consumer actif et en attente de messages...")
        logger.info("Le consumer group devrait montrer '1 Active Consumer' dans Kafka UI")
        logger.info("=" * 60)
        logger.info("")
        
        last_heartbeat_log = time.time()
        
        try:
            logger.info("[ACTIF] Consumer actif et en attente de messages...")
            logger.info("[INFO] Le consumer devrait maintenant apparaître comme '1 Active Consumer' dans Kafka UI")
            
            poll_count = 0
            while cls._running:
                try:
                    poll_count += 1
                    # Log tous les 10 polls pour confirmer que le consumer écoute
                    if poll_count % 10 == 1:
                        logger.info(f"[POLL #{poll_count}] Consumer en attente de messages...")
                    
                    # Poll avec timeout pour permettre l'arrêt propre et maintenir la connexion
                    # Le poll() est essentiel pour maintenir la connexion active
                    # Augmenter le timeout pour recevoir plus de messages par batch
                    message_pack = consumer.poll(timeout_ms=5000)
                    
                    # Afficher un heartbeat toutes les 10 secondes pour montrer qu'on est actif
                    current_time = time.time()
                    if current_time - last_heartbeat_log >= 10:
                        # Vérifier les offsets pour diagnostiquer
                        try:
                            partitions = consumer.assignment()
                            if partitions:
                                offset_info = []
                                for partition in partitions:
                                    try:
                                        earliest = consumer.beginning_offsets([partition])[partition]
                                        latest = consumer.end_offsets([partition])[partition]
                                        committed = consumer.committed(partition)
                                        position = consumer.position(partition)
                                        lag = latest - (committed if committed is not None else position) if committed is not None or position is not None else 0
                                        offset_info.append(f"P{partition.partition}: pos={position}, committed={committed}, latest={latest}, lag={lag}")
                                    except Exception as e:
                                        offset_info.append(f"P{partition.partition}: erreur={e}")
                                logger.info(f"[HEARTBEAT] Consumer actif - Poll #{poll_count} - {message_count} messages traites - Offsets: {', '.join(offset_info)}")
                            else:
                                logger.info(f"[HEARTBEAT] Consumer actif - Poll #{poll_count} - {message_count} messages traites - Aucune partition assignee")
                        except Exception as e:
                            logger.info(f"[HEARTBEAT] Consumer actif - Poll #{poll_count} - {message_count} messages traites (erreur offset: {e})")
                        last_heartbeat_log = current_time
                    
                    if message_pack:
                        logger.info(f"[RECEPTION] {len(message_pack)} partition(s) avec messages")
                        for topic_partition, messages in message_pack.items():
                            logger.info(f"[TRAITEMENT] {len(messages)} message(s) depuis {topic_partition}")
                            # Traiter tous les messages du batch
                            processed_count = 0
                            ignored_count = 0
                            error_count = 0
                            for message in messages:
                                message_count += 1
                                logger.info(f"[MESSAGE #{message_count}] Offset: {message.offset}, Partition: {message.partition}")
                                try:
                                    # Traiter le message (même s'il est ignoré, on doit avancer)
                                    cls.process_message(message)
                                    processed_count += 1
                                    logger.info(f"[SUCCES] Message #{message_count} traite avec succes")
                                except Exception as e:
                                    error_count += 1
                                    logger.error(f"[ERREUR] Erreur lors du traitement du message #{message_count}: {e}", exc_info=True)
                                    # Même en cas d'erreur, on continue pour ne pas bloquer le consumer
                                    # Le message sera commité pour éviter de rester bloqué
                            
                            logger.info(f"[BATCH] Resume: {processed_count} traites, {error_count} erreurs, {len(messages)} total")
                            
                            # Commit manuel APRÈS traitement de TOUS les messages du batch
                            # On commit même si certains messages ont été ignorés (source='django')
                            # pour réduire le lag et avancer dans le topic
                            if len(messages) > 0:
                                try:
                                    consumer.commit()
                                    logger.info(f"[COMMIT] {len(messages)} message(s) commits (traites: {processed_count}, total: {message_count})")
                                except Exception as e:
                                    logger.error(f"[ERREUR] Erreur lors du commit: {e}")
                    else:
                        # Pas de messages, mais on continue à écouter
                        # Le poll() maintient la connexion active même sans messages
                        # C'est important pour rester actif dans Kafka
                        if poll_count % 50 == 0:  # Log tous les 50 polls
                            logger.debug(f"[POLL #{poll_count}] En attente de messages (consumer actif)")
                        
                except Exception as poll_error:
                    logger.error(f"[ERREUR] Erreur dans la boucle poll #{poll_count}: {poll_error}", exc_info=True)
                    # Continuer la boucle même en cas d'erreur pour rester actif
                    time.sleep(1)
                    # Réessayer de se reconnecter
                    try:
                        # Vérifier la connexion
                        if not consumer.bootstrap_connected():
                            logger.warning("[RECONNEXION] Connexion perdue, tentative de reconnexion...")
                            # Fermer et recréer le consumer si nécessaire
                            try:
                                consumer.close()
                            except:
                                pass
                            cls._consumer = None
                            consumer = cls.get_consumer()
                            if consumer:
                                logger.info("[RECONNEXION] Reconnexion réussie")
                            else:
                                logger.error("[RECONNEXION] Impossible de recréer le consumer")
                        else:
                            logger.info("[RECONNEXION] Connexion toujours active")
                    except Exception as recon_error:
                        logger.error(f"[RECONNEXION] Erreur lors de la reconnexion: {recon_error}")
                        # Attendre un peu avant de réessayer
                        time.sleep(2)
                        
        except KeyboardInterrupt:
            logger.info("[ARRET] Arret demande par l'utilisateur (Ctrl+C)")
        except Exception as e:
            logger.error(f"[ERREUR] Erreur dans la boucle de consommation: {e}", exc_info=True)
        finally:
            cls._running = False
            logger.info("[ARRET] Arret du consumer en cours...")
            if consumer:
                try:
                    consumer.close()
                    logger.info("[ARRET] Consumer ferme")
                except Exception as e:
                    logger.error(f"[ERREUR] Erreur lors de la fermeture: {e}")
                cls._consumer = None
            logger.info("=" * 60)
            logger.info(f"CONSUMER KAFKA ARRETE")
            logger.info(f"Total messages traites: {message_count}")
            logger.info("=" * 60)
        
        return True
    
    @classmethod
    def stop_consuming(cls):
        """Arrêter la consommation des messages Kafka"""
        if not cls._running:
            return
        
        cls._running = False
        if cls._consumer:
            cls._consumer.close()
            cls._consumer = None
        if cls._thread:
            cls._thread.join(timeout=5)
        logger.info("Consumer Kafka arrêté")
