"""
Script pour inspecter les messages Kafka en attente
"""
import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer
from django.conf import settings
import json

def inspect_messages():
    """Inspecter les messages dans le topic Kafka"""
    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9094')
    topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
    group_id = 'django-reservation-consumer-group'
    
    print(f"Connexion à Kafka: {bootstrap_servers}")
    print(f"Topic: {topic}")
    print(f"Group ID: {group_id}")
    print("=" * 60)
    
    # Utiliser un consumer temporaire SANS group_id pour lire tous les messages
    # Cela nous permet de voir les messages sans affecter l'offset du consumer principal
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[bootstrap_servers],
        # Pas de group_id pour lire tous les messages
        auto_offset_reset='earliest',  # Lire depuis le début
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
        key_deserializer=lambda k: k.decode('utf-8') if k else None,
        consumer_timeout_ms=10000,  # Timeout après 10 secondes
    )
    
    # Obtenir les partitions
    partitions = consumer.partitions_for_topic(topic)
    print(f"Partitions trouvées: {partitions}")
    
    print("Lecture des messages...")
    print("=" * 60)
    
    message_count = 0
    django_messages = 0
    spring_messages = 0
    other_messages = 0
    
    try:
        for message in consumer:
            message_count += 1
            data = message.value
            
            if data:
                source = data.get('source', 'unknown')
                action = data.get('action', 'unknown')
                uuid_str = data.get('uuid', 'N/A')
                
                if source == 'django':
                    django_messages += 1
                    print(f"[{message_count}] DJANGO - Action: {action}, UUID: {uuid_str[:8]}...")
                elif source == 'spring' or source == 'spring-boot':
                    spring_messages += 1
                    print(f"[{message_count}] SPRING - Action: {action}, UUID: {uuid_str[:8]}...")
                    print(f"  Données: {json.dumps(data, indent=2, default=str)}")
                else:
                    other_messages += 1
                    print(f"[{message_count}] AUTRE (source={source}) - Action: {action}, UUID: {uuid_str[:8]}...")
                    print(f"  Données: {json.dumps(data, indent=2, default=str)}")
                
                if message_count >= 20:  # Limiter à 20 messages pour l'affichage
                    print("...")
                    break
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        consumer.close()
    
    print("=" * 60)
    print(f"Résumé:")
    print(f"  Total messages inspectés: {message_count}")
    print(f"  Messages Django: {django_messages}")
    print(f"  Messages Spring Boot: {spring_messages}")
    print(f"  Autres messages: {other_messages}")
    print("=" * 60)

if __name__ == '__main__':
    inspect_messages()
