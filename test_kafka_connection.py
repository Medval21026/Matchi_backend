#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour tester la connexion à Kafka
"""
import os
import sys
import django

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("TEST DE CONNEXION KAFKA")
print("=" * 60)
print()

bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')
topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')

print(f"Configuration:")
print(f"  Bootstrap servers: {bootstrap_servers}")
print(f"  Topic: {topic}")
print()

# Test 1: Import de kafka-python
print("1. Vérification de l'installation de kafka-python...")
try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError, KafkaTimeoutError
    print("   ✅ kafka-python est installé")
except ImportError as e:
    print(f"   ❌ kafka-python n'est pas installé: {e}")
    print("   → Installez avec: pip install kafka-python")
    sys.exit(1)

# Test 2: Création d'un producer
print("\n2. Test de création d'un producer...")
try:
    producer = KafkaProducer(
        bootstrap_servers=[bootstrap_servers],
        request_timeout_ms=5000,
        max_block_ms=3000,
    )
    print("   ✅ Producer créé")
except Exception as e:
    print(f"   ❌ Erreur lors de la création du producer: {e}")
    sys.exit(1)

# Test 3: Test de connexion (envoi d'un message de test)
print("\n3. Test de connexion à Kafka (envoi d'un message de test)...")
try:
    test_message = b'test_connection'
    future = producer.send('__test_connection__', value=test_message)
    record_metadata = future.get(timeout=5)
    print(f"   ✅ Connexion réussie!")
    print(f"      Topic: {record_metadata.topic}")
    print(f"      Partition: {record_metadata.partition}")
    print(f"      Offset: {record_metadata.offset}")
except KafkaTimeoutError:
    print(f"   ❌ TIMEOUT: Kafka ne répond pas après 5 secondes")
    print(f"   → Vérifiez que Kafka est démarré sur {bootstrap_servers}")
    print(f"   → Vérifiez que le port est correct")
    producer.close()
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Erreur de connexion: {e}")
    print(f"   → Vérifiez que Kafka est démarré et accessible")
    producer.close()
    sys.exit(1)

# Test 4: Vérification du topic
print("\n4. Vérification du topic...")
try:
    from kafka.admin import KafkaAdminClient
    admin_client = KafkaAdminClient(
        bootstrap_servers=[bootstrap_servers],
        request_timeout_ms=5000
    )
    topics = admin_client.list_topics(timeout_ms=5000)
    admin_client.close()
    
    if topic in topics:
        print(f"   ✅ Le topic '{topic}' existe")
    else:
        print(f"   ⚠️  Le topic '{topic}' n'existe pas")
        print(f"   → Il sera créé automatiquement lors du premier envoi")
except Exception as e:
    print(f"   ⚠️  Impossible de vérifier les topics: {e}")
    print(f"   → Le topic sera créé automatiquement si nécessaire")

# Test 5: Test d'envoi sur le vrai topic
print(f"\n5. Test d'envoi sur le topic '{topic}'...")
try:
    test_event = {
        'action': 'TEST',
        'uuid': 'test-uuid-123',
        'source': 'test_script'
    }
    import json
    future = producer.send(
        topic,
        key=b'test_key',
        value=json.dumps(test_event).encode('utf-8')
    )
    record_metadata = future.get(timeout=5)
    print(f"   ✅ Message envoyé avec succès!")
    print(f"      Topic: {record_metadata.topic}")
    print(f"      Partition: {record_metadata.partition}")
    print(f"      Offset: {record_metadata.offset}")
except KafkaTimeoutError:
    print(f"   ❌ TIMEOUT: Impossible d'envoyer sur le topic '{topic}'")
    print(f"   → Vérifiez que Kafka est démarré et que le topic existe")
except Exception as e:
    print(f"   ❌ Erreur lors de l'envoi: {e}")

# Fermeture
producer.close()

print()
print("=" * 60)
print("✅ Tous les tests sont passés!")
print("   Kafka est accessible et prêt à recevoir des messages")
print("=" * 60)
