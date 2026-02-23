# Guide de Résolution - Connexion Kafka Django

## Problème
Le consumer Django ne peut pas se connecter à Kafka (`NoBrokersAvailable`), donc le consumer group n'est pas créé.

## Diagnostic
- Les ports 9092 et 9094 sont ouverts
- Mais Kafka n'est pas accessible depuis Python
- Kafka UI fonctionne sur `localhost:8080`

## Solutions

### Solution 1: Vérifier la configuration Kafka (Docker)

Si Kafka est dans Docker, vérifiez les ports exposés :

```bash
docker ps
# Cherchez les ports Kafka, par exemple: 0.0.0.0:9094->9094/tcp
```

### Solution 2: Vérifier les listeners Kafka

Dans la configuration Kafka (`server.properties` ou `docker-compose.yml`), vérifiez :

```properties
# Pour Docker
listeners=PLAINTEXT://0.0.0.0:9094
advertised.listeners=PLAINTEXT://localhost:9094

# OU si Kafka est dans un réseau Docker
advertised.listeners=PLAINTEXT://host.docker.internal:9094
```

### Solution 3: Utiliser l'adresse IP au lieu de localhost

Essayez avec `127.0.0.1` au lieu de `localhost` :

```python
KAFKA_BOOTSTRAP_SERVERS = '127.0.0.1:9094'
```

### Solution 4: Vérifier le réseau Docker

Si Kafka est dans Docker et Django sur Windows :

```yaml
# docker-compose.yml
services:
  kafka:
    ports:
      - "9094:9094"
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9094
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9094
```

## Test de connexion

Une fois la configuration corrigée, testez :

```bash
python find_kafka_port.py
```

Puis redémarrez le consumer :

```bash
python manage.py kafka_consumer
```

Le consumer group `django-reservation-consumer-group` devrait apparaître dans Kafka UI.
