"""
Script de diagnostic pour vérifier la connexion Kafka et créer le consumer group
"""
import sys
import os
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import json

def test_kafka_connection():
    print("=" * 60)
    print("DIAGNOSTIC KAFKA - CREATION CONSUMER GROUP DJANGO")
    print("=" * 60)
    
    # Tester différents ports
    ports = [9092, 9093, 9094, 9095]
    bootstrap_servers = None
    
    print("\n[1/5] Test de connexion aux ports Kafka...")
    for port in ports:
        try:
            test_consumer = KafkaConsumer(
                bootstrap_servers=[f'localhost:{port}'],
                consumer_timeout_ms=2000
            )
            test_consumer.bootstrap_connected()
            print(f"  ✅ Port {port} accessible")
            bootstrap_servers = f'localhost:{port}'
            test_consumer.close()
            break
        except Exception as e:
            print(f"  [ERREUR] Port {port} non accessible: {type(e).__name__}")
    
    if not bootstrap_servers:
        print("\n❌ Aucun port Kafka accessible!")
        print("\nVérifications:")
        print("  1. Kafka est-il démarré?")
        print("  2. Les ports sont-ils corrects?")
        print("  3. Kafka est-il dans Docker? Vérifiez les ports exposés")
        return False
    
    print(f"\n✅ Port Kafka trouvé: {bootstrap_servers}")
    
    # Tester la création du consumer group
    print("\n[2/5] Création du consumer group Django...")
    group_id = 'django-reservation-consumer-group'
    topic = 'horaire-sync-topic'
    
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            consumer_timeout_ms=5000,
        )
        
        print(f"  ✅ Consumer créé")
        
        # S'abonner au topic
        print(f"\n[3/5] Abonnement au topic '{topic}'...")
        consumer.subscribe([topic])
        print(f"  ✅ Abonné au topic")
        
        # Tester la connexion
        print(f"\n[4/5] Test de connexion...")
        consumer.bootstrap_connected()
        print(f"  ✅ Connecté au broker")
        
        # Faire un poll pour créer le consumer group
        print(f"\n[5/5] Création du consumer group (poll)...")
        print(f"  En attente de messages (5 secondes)...")
        message_pack = consumer.poll(timeout_ms=5000)
        
        if message_pack:
            print(f"  ✅ Messages reçus: {len(message_pack)} partitions")
            for tp, messages in message_pack.items():
                print(f"     - {tp}: {len(messages)} messages")
        else:
            print(f"  ✅ Aucun message (normal), mais consumer group créé")
        
        # Récupérer les partitions
        partitions = consumer.assignment()
        print(f"  ✅ Partitions assignées: {partitions}")
        
        print("\n" + "=" * 60)
        print("✅ CONSUMER GROUP CRÉÉ AVEC SUCCÈS!")
        print("=" * 60)
        print(f"Consumer Group ID: {group_id}")
        print(f"Topic: {topic}")
        print(f"Bootstrap Servers: {bootstrap_servers}")
        print("\n💡 Vérifiez dans Kafka UI:")
        print(f"   - Allez dans: Topics / {topic} / Consumers")
        print(f"   - Cherchez: {group_id}")
        print(f"   - Le group devrait apparaître maintenant")
        
        consumer.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_kafka_connection()
    sys.exit(0 if success else 1)
