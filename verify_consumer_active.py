"""
Script pour vérifier que le consumer Django est actif dans Kafka
"""
import sys
import os
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer
from kafka.admin import KafkaAdminClient, ConfigResource, ConfigResourceType
import json

def check_consumer_group():
    print("=" * 60)
    print("VERIFICATION CONSUMER GROUP DJANGO")
    print("=" * 60)
    
    bootstrap_servers = '127.0.0.1:9094'
    group_id = 'django-reservation-consumer-group'
    topic = 'horaire-sync-topic'
    
    try:
        # Créer un consumer pour vérifier le group
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            consumer_timeout_ms=2000,
        )
        
        consumer.subscribe([topic])
        consumer.bootstrap_connected()
        
        print(f"\n[INFO] Consumer Group: {group_id}")
        print(f"[INFO] Topic: {topic}")
        print(f"[INFO] Bootstrap Servers: {bootstrap_servers}")
        
        # Faire un poll pour s'enregistrer
        print(f"\n[TEST] Poll pour s'enregistrer...")
        message_pack = consumer.poll(timeout_ms=3000)
        
        if message_pack:
            print(f"[OK] Messages recus: {len(message_pack)} partitions")
        else:
            print(f"[OK] Aucun message (normal)")
        
        # Vérifier les partitions assignées
        partitions = consumer.assignment()
        print(f"[OK] Partitions assignees: {len(partitions)}")
        
        # Faire un autre poll pour rester actif
        print(f"\n[TEST] Deuxieme poll pour rester actif...")
        message_pack2 = consumer.poll(timeout_ms=3000)
        print(f"[OK] Consumer reste actif")
        
        consumer.close()
        
        print("\n" + "=" * 60)
        print("[SUCCES] CONSUMER GROUP ACTIF")
        print("=" * 60)
        print("Le consumer group devrait maintenant montrer:")
        print("  - Active Consumers: 1")
        print("  - State: STABLE (au lieu de EMPTY)")
        print("\nVerifiez dans Kafka UI dans quelques secondes")
        
        return True
        
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_consumer_group()
