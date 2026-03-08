#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour vérifier les indisponibilités non synchronisées
"""
import os
import sys
import django

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from reservations.models import Indisponibilites
from django.utils import timezone
from datetime import timedelta
from django.db import models

print("=" * 60)
print("DIAGNOSTIC DES INDISPONIBILITÉS NON SYNCHRONISÉES")
print("=" * 60)
print()

# Vérifier si les champs existent
try:
    test = Indisponibilites.objects.first()
    if test:
        has_kafka_synced = hasattr(test, 'kafka_synced')
        has_last_attempt = hasattr(test, 'last_kafka_sync_attempt')
        print(f"✅ Champs Kafka: kafka_synced={has_kafka_synced}, last_kafka_sync_attempt={has_last_attempt}")
    else:
        print("⚠️ Aucune indisponibilité dans la base de données")
        sys.exit(0)
except Exception as e:
    print(f"❌ Erreur lors de la vérification des champs: {e}")
    print("   → La migration n'a peut-être pas été appliquée")
    print("   → Exécutez: python manage.py migrate reservations")
    sys.exit(1)

# Statistiques générales
total = Indisponibilites.objects.count()
print(f"\n📊 Statistiques générales:")
print(f"   Total d'indisponibilités: {total}")

if total == 0:
    print("\n✅ Aucune indisponibilité dans la base de données")
    sys.exit(0)

try:
    synced = Indisponibilites.objects.filter(kafka_synced=True).count()
    unsynced = Indisponibilites.objects.filter(kafka_synced=False).count()
    print(f"   Synchronisées (kafka_synced=True): {synced}")
    print(f"   Non synchronisées (kafka_synced=False): {unsynced}")
except Exception as e:
    print(f"❌ Erreur lors du comptage: {e}")
    sys.exit(1)

# Indisponibilités non synchronisées
print(f"\n🔍 Indisponibilités non synchronisées:")
try:
    unsynced_list = Indisponibilites.objects.filter(kafka_synced=False).order_by('-id')[:10]
    count = unsynced_list.count()
    
    if count == 0:
        print("   ✅ Toutes les indisponibilités sont synchronisées")
    else:
        print(f"   Trouvé {count} indisponibilité(s) non synchronisée(s) (affichage des 10 premières):")
        print()
        for ind in unsynced_list:
            last_attempt = ind.last_kafka_sync_attempt.strftime('%Y-%m-%d %H:%M:%S') if ind.last_kafka_sync_attempt else "Jamais"
            print(f"   - UUID: {ind.uuid}")
            print(f"     Terrain: {ind.terrain.nom_fr if ind.terrain else 'N/A'} (ID: {ind.terrain.id if ind.terrain else 'N/A'})")
            print(f"     Date: {ind.date_indisponibilite}")
            print(f"     Heure: {ind.heure_debut} - {ind.heure_fin}")
            print(f"     Dernière tentative: {last_attempt}")
            print(f"     kafka_synced: {ind.kafka_synced}")
            print()
        
        # Vérifier celles qui peuvent être synchronisées maintenant
        min_interval = timezone.now() - timedelta(minutes=5)
        can_sync = Indisponibilites.objects.filter(
            kafka_synced=False
        ).filter(
            models.Q(last_kafka_sync_attempt__isnull=True) | 
            models.Q(last_kafka_sync_attempt__lt=min_interval)
        ).count()
        
        print(f"   📌 Indisponibilités prêtes pour synchronisation (pas tentées depuis 5 min): {can_sync}")
        
except Exception as e:
    print(f"❌ Erreur lors de la récupération: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Pour tester le rattrapage manuellement:")
print("  python manage.py shell")
print("  >>> from reservations.services.kafka_service import KafkaService")
print("  >>> stats = KafkaService.sync_unsynced_indisponibilites()")
print("  >>> print(stats)")
print("=" * 60)
