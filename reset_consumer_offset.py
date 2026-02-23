"""
Script pour réinitialiser l'offset du consumer group Django
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from kafka import KafkaConsumer, TopicPartition
from django.conf import settings

def reset_consumer_offset():
    """Réinitialiser l'offset du consumer group à 'earliest'"""
    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9094')
    topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
    group_id = 'django-reservation-consumer-group'
    
    print("=" * 60)
    print("REINITIALISATION DE L'OFFSET DU CONSUMER GROUP")
    print("=" * 60)
    print(f"Bootstrap servers: {bootstrap_servers}")
    print(f"Topic: {topic}")
    print(f"Group ID: {group_id}")
    print("")
    
    try:
        # Créer un consumer temporaire pour réinitialiser l'offset
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            consumer_timeout_ms=2000,
        )
        
        print("[1/4] Connexion a Kafka...")
        consumer.bootstrap_connected()
        print("[OK] Connecte")
        
        print(f"[2/4] Abonnement au topic '{topic}'...")
        consumer.subscribe([topic])
        print("[OK] Abonne")
        
        # Attendre l'assignation des partitions
        import time
        time.sleep(2)
        
        print("[3/4] Recuperation des partitions...")
        partitions = consumer.assignment()
        print(f"[OK] Partitions assignees: {partitions}")
        
        if not partitions:
            print("[ERREUR] Aucune partition assignee!")
            consumer.close()
            return
        
        print("[4/4] Repositionnement a l'offset earliest...")
        # Obtenir les offsets earliest et latest pour chaque partition
        for partition in partitions:
            # Obtenir les offsets earliest et latest
            earliest_offset = consumer.beginning_offsets([partition])[partition]
            latest_offset = consumer.end_offsets([partition])[partition]
            
            print(f"  Partition {partition.partition}: earliest={earliest_offset}, latest={latest_offset}")
            
            # Se repositionner au début
            consumer.seek(partition, earliest_offset)
            print(f"  [OK] Repositionne a l'offset {earliest_offset}")
        
        # Faire un commit pour sauvegarder la nouvelle position
        consumer.commit()
        print("[OK] Offset commit")
        
        consumer.close()
        print("")
        print("=" * 60)
        print("[SUCCES] OFFSET REINITIALISE")
        print("=" * 60)
        print("Le consumer Django devrait maintenant recevoir tous les messages")
        print("depuis le debut du topic.")
        
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    reset_consumer_offset()
