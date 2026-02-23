"""
Script pour trouver le port Kafka qui fonctionne
"""
import socket
from kafka import KafkaConsumer
import sys

def test_port(host, port):
    """Tester si un port est ouvert"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_kafka_connection(bootstrap_servers):
    """Tester la connexion Kafka"""
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            consumer_timeout_ms=2000
        )
        consumer.bootstrap_connected()
        consumer.close()
        return True
    except:
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("RECHERCHE DU PORT KAFKA")
    print("=" * 60)
    
    ports = [9092, 9093, 9094, 9095, 29092, 29093, 29094]
    host = 'localhost'
    
    print(f"\nTest des ports sur {host}:")
    working_port = None
    
    for port in ports:
        print(f"\nTest port {port}...")
        if test_port(host, port):
            print(f"  [OK] Port {port} est ouvert")
            if test_kafka_connection(f"{host}:{port}"):
                print(f"  [SUCCES] Kafka accessible sur {host}:{port}")
                working_port = port
                break
            else:
                print(f"  [ERREUR] Port ouvert mais Kafka non accessible")
        else:
            print(f"  [FERME] Port {port} est ferme")
    
    if working_port:
        print("\n" + "=" * 60)
        print("PORT KAFKA TROUVE!")
        print("=" * 60)
        print(f"Port: {working_port}")
        print(f"\nMettez a jour settings.py:")
        print(f"  KAFKA_BOOTSTRAP_SERVERS = 'localhost:{working_port}'")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("AUCUN PORT KAFKA TROUVE")
        print("=" * 60)
        print("Verifications:")
        print("  1. Kafka est-il demarre?")
        print("  2. Si Kafka est dans Docker, verifiez les ports exposes")
        print("  3. Verifiez la configuration listeners dans Kafka")
