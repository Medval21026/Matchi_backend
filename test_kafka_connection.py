"""
Script de diagnostic pour tester la connexion Kafka
"""
import sys
import socket
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

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
    """Tester la connexion à Kafka"""
    print(f"\n[TEST] Connexion a Kafka sur {bootstrap_servers}...")
    
    # Extraire host et port
    try:
        if ':' in bootstrap_servers:
            host, port = bootstrap_servers.split(':')
            port = int(port)
        else:
            host = bootstrap_servers
            port = 9092
    except:
        print(f"[ERREUR] Format invalide: {bootstrap_servers}")
        return False
    
    # Test 1: Vérifier si le port est ouvert
    print(f"  1. Test du port {port} sur {host}...")
    if test_port(host, port):
        print(f"     [OK] Port {port} est ouvert")
    else:
        print(f"     [ERREUR] Port {port} est ferme ou inaccessible")
        return False
    
    # Test 2: Tester la connexion Kafka
    print(f"  2. Test de la connexion Kafka...")
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=[bootstrap_servers],
            consumer_timeout_ms=2000,
            api_version=(0, 10, 1)
        )
        consumer.bootstrap_connected()
        print(f"     [OK] Connexion Kafka reussie!")
        consumer.close()
        return True
    except Exception as e:
        print(f"     [ERREUR] Erreur de connexion: {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("DIAGNOSTIC DE CONNEXION KAFKA")
    print("=" * 60)
    
    # Tester différents ports communs
    ports_to_test = [9092, 9093, 9094, 9095]
    host = 'localhost'
    
    print(f"\n[INFO] Test des ports Kafka sur {host}:")
    open_ports = []
    for port in ports_to_test:
        if test_port(host, port):
            print(f"  [OK] Port {port} est ouvert")
            open_ports.append(port)
        else:
            print(f"  [FERME] Port {port} est ferme")
    
    if not open_ports:
        print("\n[ATTENTION] Aucun port Kafka n'est ouvert sur localhost")
        print("\nSuggestions:")
        print("  1. Verifiez que Kafka est demarre")
        print("  2. Verifiez la configuration Kafka (server.properties)")
        print("  3. Si Kafka est dans Docker, verifiez les ports exposes")
        print("  4. Verifiez les parametres listeners et advertised.listeners dans Kafka")
        sys.exit(1)
    
    print(f"\n[INFO] Test de connexion Kafka sur les ports ouverts:")
    success = False
    for port in open_ports:
        if test_kafka_connection(f"{host}:{port}"):
            print(f"\n[SUCCES] Kafka est accessible sur {host}:{port}")
            print(f"\nMettez a jour KAFKA_BOOTSTRAP_SERVERS dans settings.py:")
            print(f"   KAFKA_BOOTSTRAP_SERVERS = '{host}:{port}'")
            success = True
            break
    
    if not success:
        print("\n[ERREUR] Aucune connexion Kafka reussie")
        print("\nVerifiez:")
        print("  1. La configuration listeners dans server.properties de Kafka")
        print("  2. Les parametres advertised.listeners")
        print("  3. Si Kafka est dans Docker, les ports exposes et le reseau")
