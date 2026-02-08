#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script simple pour tester la connexion à la base de données"""

import os
import sys

# Charger .env AVANT d'importer Django
from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("Variables d'environnement chargées:")
print(f"MYSQLHOST: {os.getenv('MYSQLHOST', 'NOT SET')}")
print(f"MYSQLDATABASE: {os.getenv('MYSQLDATABASE', 'NOT SET')}")
print(f"MYSQLUSER: {os.getenv('MYSQLUSER', 'NOT SET')}")
print(f"MYSQLPORT: {os.getenv('MYSQLPORT', 'NOT SET')}")
print(f"MYSQL_URL: {os.getenv('MYSQL_URL', 'NOT SET')}")
print("=" * 50)

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')

try:
    import django
    django.setup()
    
    from django.db import connection
    
    print("\nTentative de connexion à la base de données...")
    connection.ensure_connection()
    
    print("✅ Connexion réussie!")
    print(f"Base de données: {connection.settings_dict['NAME']}")
    print(f"Host: {connection.settings_dict['HOST']}")
    print(f"User: {connection.settings_dict['USER']}")
    print(f"Port: {connection.settings_dict['PORT']}")
    
except Exception as e:
    print(f"\n❌ Erreur de connexion: {e}")
    print(f"Type d'erreur: {type(e).__name__}")
    sys.exit(1)
