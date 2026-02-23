"""
Script pour vérifier le format des messages dans Kafka
"""
import sys
import os
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer
import json

print("=" * 60)
print("VERIFICATION DES MESSAGES KAFKA")
print("=" * 60)

bootstrap_servers = '127.0.0.1:9094'
topic = 'horaire-sync-topic'

try:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[bootstrap_servers],
        group_id='test-inspect-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
        auto_offset_reset='latest',  # Lire seulement les nouveaux messages
        consumer_timeout_ms=5000,
    )
    
    print(f"\nEn attente de nouveaux messages (5 secondes)...")
    print("(Si aucun message n'arrive, on va lire les derniers messages)")
    
    message_pack = consumer.poll(timeout_ms=5000)
    
    if not message_pack:
        # Lire depuis le début pour voir les messages existants
        print("\nAucun nouveau message, lecture des derniers messages...")
        consumer.close()
        
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[bootstrap_servers],
            group_id='test-inspect-group-2',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
            auto_offset_reset='latest',
            consumer_timeout_ms=2000,
        )
        
        # Se positionner à la fin et lire les 5 derniers messages
        partitions = consumer.assignment()
        if partitions:
            for tp in partitions:
                # Obtenir les métadonnées pour connaître le dernier offset
                end_offsets = consumer.end_offsets([tp])
                end_offset = end_offsets.get(tp, 0)
                if end_offset > 0:
                    # Lire les 5 derniers messages
                    start_offset = max(0, end_offset - 5)
                    consumer.seek(tp, start_offset)
        
        message_pack = consumer.poll(timeout_ms=3000)
    
    if message_pack:
        print(f"\n[OK] {len(message_pack)} partition(s) avec messages\n")
        message_count = 0
        for topic_partition, messages in message_pack.items():
            for message in list(messages)[-5:]:  # Derniers 5 messages
                message_count += 1
                data = message.value
                print(f"Message #{message_count}:")
                print(f"  Offset: {message.offset}")
                print(f"  Partition: {message.partition}")
                print(f"  Source: {data.get('source', 'N/A')}")
                print(f"  Action: {data.get('action', 'N/A')}")
                print(f"  UUID: {data.get('uuid', 'N/A')}")
                print(f"  TerrainId: {data.get('terrainId', 'N/A')}")
                print(f"  Donnees completes:")
                print(json.dumps(data, indent=4, default=str))
                print("-" * 60)
    else:
        print("\n[AUCUN MESSAGE] Aucun message trouve dans le topic")
    
    consumer.close()
    
except Exception as e:
    print(f"\n[ERREUR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
