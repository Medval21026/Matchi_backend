"""
Commande Django pour démarrer le consumer Kafka
Usage: python manage.py kafka_consumer
"""
from django.core.management.base import BaseCommand
from reservations.services.kafka_consumer import KafkaConsumerService
import signal
import sys
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Démarre le consumer Kafka pour écouter les événements de synchronisation'

    def handle(self, *args, **options):
        from django.conf import settings
        
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9094')
        topic = getattr(settings, 'KAFKA_TOPIC', 'horaire-sync-topic')
        
        self.stdout.write(self.style.SUCCESS('Démarrage du consumer Kafka...'))
        self.stdout.write(f'\nConfiguration:')
        self.stdout.write(f'  - Bootstrap servers: {bootstrap_servers}')
        self.stdout.write(f'  - Topic: {topic}')
        self.stdout.write(f'  - Group ID: django-reservation-consumer-group')
        self.stdout.write(f'\n[INFO] Connexion à Kafka...')
        
        # Gérer l'arrêt propre avec Ctrl+C
        def signal_handler(sig, frame):
            self.stdout.write(self.style.WARNING('\nArrêt du consumer Kafka...'))
            KafkaConsumerService.stop_consuming()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Démarrer le consumer (bloquant)
            success = KafkaConsumerService.start_consuming()
            
            if not success:
                self.stdout.write(self.style.ERROR('\n[ERREUR] Impossible de demarrer le consumer Kafka.'))
                self.stdout.write(self.style.WARNING('\nVerifications:'))
                self.stdout.write(f'  1. Kafka est-il demarre sur {bootstrap_servers}?')
                self.stdout.write(f'  2. Le port est-il correct?')
                self.stdout.write(f'  3. Le topic "{topic}" existe-t-il?')
                return
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nArrêt du consumer Kafka...'))
            KafkaConsumerService.stop_consuming()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErreur: {e}'))
            KafkaConsumerService.stop_consuming()
            raise
