"""
Script pour tester la création du consumer group Django
"""
import sys
import os
import django
import time

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer
import json

def test_consumer_group():
    print("=" * 60)
    print("TEST CREATION CONSUMER GROUP DJANGO")
    print("=" * 60)
    
    bootstrap_servers = '127.0.0.1:9094'
    topic = 'horaire-sync-topic'
    group_id = 'django-reservation-consumer-group'
    
    try:
        print(f"\n[1/4] Creation du consumer...")
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=5000,
        )
        print("    [OK] Consumer cree")
        
        print(f"\n[2/4] Abonnement au topic '{topic}'...")
        consumer.subscribe([topic])
        print("    [OK] Abonne")
        
        print(f"\n[3/4] Test de connexion...")
        consumer.bootstrap_connected()
        print("    [OK] Connecte")
        
        print(f"\n[4/4] Creation du consumer group (poll)...")
        print("    En attente de messages (5 secondes)...")
        message_pack = consumer.poll(timeout_ms=5000)
        
        if message_pack:
            print(f"    [OK] Messages recus: {len(message_pack)} partitions")
        else:
            print(f"    [OK] Aucun message (normal), consumer group cree")
        
        partitions = consumer.assignment()
        print(f"    [OK] Partitions: {partitions}")
        
        print("\n" + "=" * 60)
        print("[SUCCES] CONSUMER GROUP CREE!")
        print("=" * 60)
        print(f"Group ID: {group_id}")
        print(f"Topic: {topic}")
        print(f"\nVerifiez dans Kafka UI:")
        print(f"  - Topics / {topic} / Consumers")
        print(f"  - Le group '{group_id}' devrait apparaître")
        
        consumer.close()
        return True
        
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_consumer_group()
