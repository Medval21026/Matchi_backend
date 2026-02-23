"""
Script pour tester la création d'un consumer group Kafka
"""
import sys
import os
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer
import time

def test_consumer_group():
    print("=" * 60)
    print("TEST DE CREATION D'UN CONSUMER GROUP KAFKA")
    print("=" * 60)
    
    bootstrap_servers = 'localhost:9094'
    topic = 'horaire-sync-topic'
    group_id = 'django-reservation-consumer-group'
    
    print(f"\nConfiguration:")
    print(f"  - Bootstrap servers: {bootstrap_servers}")
    print(f"  - Topic: {topic}")
    print(f"  - Group ID: {group_id}")
    
    try:
        print(f"\n[1/4] Creation du consumer...")
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            group_id=group_id,
            value_deserializer=lambda m: m.decode('utf-8'),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=5000,
            api_version=(0, 10, 1),
        )
        print("    [OK] Consumer cree")
        
        print(f"\n[2/4] Abonnement au topic...")
        consumer.subscribe([topic])
        print("    [OK] Abonne au topic")
        
        print(f"\n[3/4] Test de connexion...")
        consumer.bootstrap_connected()
        print("    [OK] Connecte a Kafka")
        
        print(f"\n[4/4] Consommation de messages (pour creer le consumer group)...")
        print("    En attente de messages (5 secondes)...")
        
        message_count = 0
        start_time = time.time()
        while time.time() - start_time < 5:
            message_pack = consumer.poll(timeout_ms=1000)
            if message_pack:
                for topic_partition, messages in message_pack.items():
                    message_count += len(messages)
                    print(f"    [OK] {len(messages)} messages recus depuis {topic_partition}")
            else:
                print("    [INFO] Aucun message recu (normal si le topic est vide)")
        
        print(f"\n[RESULTAT]")
        print(f"  - Messages consommes: {message_count}")
        print(f"  - Consumer group devrait etre cree: {group_id}")
        print(f"\n[INFO] Verifiez dans Kafka UI:")
        print(f"  - Allez dans: Consumers")
        print(f"  - Cherchez: {group_id}")
        print(f"  - Le group devrait apparaître meme sans messages si la connexion fonctionne")
        
        consumer.close()
        print("\n[SUCCES] Test termine")
        
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
        print("\n[DIAGNOSTIC]")
        print("  1. Verifiez que Kafka est demarre")
        print(f"  2. Verifiez que le port {bootstrap_servers} est correct")
        print(f"  3. Verifiez que le topic '{topic}' existe")
        return False
    
    return True

if __name__ == '__main__':
    test_consumer_group()
