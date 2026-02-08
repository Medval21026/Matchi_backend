#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer la base de données 'cite' et exécuter les migrations sur Railway
À exécuter via: railway run python creer_database_et_migrer.py
"""

import os
import sys
import django

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reservation_cite.settings')
django.setup()

from django.db import connection
import mysql.connector
from mysql.connector import Error

print("=" * 60)
print("CRÉATION DE LA BASE DE DONNÉES ET MIGRATIONS")
print("=" * 60)

# Récupérer les paramètres de connexion
db_host = os.getenv('MYSQLHOST', 'localhost')
db_user = os.getenv('MYSQLUSER', 'root')
db_password = os.getenv('MYSQLPASSWORD', '')
db_port = int(os.getenv('MYSQLPORT', '3306'))
db_name = os.getenv('MYSQLDATABASE', 'cite')

print(f"\n📊 Configuration:")
print(f"   Host: {db_host}")
print(f"   User: {db_user}")
print(f"   Port: {db_port}")
print(f"   Database: {db_name}")

# Étape 1 : Créer la base de données si elle n'existe pas
print(f"\n🔧 Étape 1 : Création de la base de données '{db_name}'...")
try:
    # Se connecter sans spécifier de base de données
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        port=db_port
    )
    cursor = conn.cursor()
    
    # Créer la base de données si elle n'existe pas
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"   ✅ Base de données '{db_name}' créée ou déjà existante")
    
    # Vérifier que la base existe
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor.fetchall()]
    if db_name in databases:
        print(f"   ✅ Base de données '{db_name}' vérifiée")
    else:
        print(f"   ❌ Erreur : Base de données '{db_name}' non trouvée")
        sys.exit(1)
    
    cursor.close()
    conn.close()
    
except Error as e:
    error_msg = str(e).lower()
    # Si l'erreur indique que la base existe déjà, continuer
    if 'database exists' in error_msg or 'already exists' in error_msg:
        print(f"   ℹ️  La base de données '{db_name}' existe déjà, continuation...")
    else:
        print(f"   ⚠️  Erreur lors de la création de la base de données: {e}")
        print(f"   ℹ️  Tentative de continuation avec les migrations...")
    # Ne pas bloquer le déploiement, continuer avec les migrations

# Étape 2 : Exécuter les migrations
print(f"\n🔧 Étape 2 : Exécution des migrations...")
try:
    from django.core.management import call_command
    
    # Afficher les migrations en attente avant d'exécuter
    print(f"   📋 Vérification des migrations en attente...")
    call_command('showmigrations', '--list', verbosity=1)
    
    # Exécuter les migrations avec verbosité maximale
    print(f"\n   🔄 Application des migrations...")
    call_command('migrate', '--noinput', verbosity=2)
    
    # Forcer les migrations de l'application reservations si nécessaire
    print(f"\n   🔄 Application spécifique des migrations 'reservations'...")
    call_command('migrate', 'reservations', '--noinput', verbosity=2)
    
    print(f"   ✅ Migrations exécutées avec succès")
except Exception as e:
    print(f"   ❌ Erreur lors des migrations: {e}")
    import traceback
    traceback.print_exc()
    # Les migrations doivent réussir, sinon le déploiement échoue
    print(f"   ❌ Les migrations ont échoué, le déploiement sera arrêté")
    sys.exit(1)

# Étape 3 : Vérifier les migrations appliquées
print(f"\n🔧 Étape 3 : Vérification des migrations...")
try:
    from django.core.management import call_command
    print(f"   📋 Liste complète des migrations:")
    call_command('showmigrations', verbosity=1)
except Exception as e:
    print(f"   ⚠️  Erreur lors de la vérification: {e}")

# Étape 4 : Vérifier la base de données utilisée par Django
print(f"\n🔧 Étape 4 : Vérification de la base de données Django...")
try:
    db_config = connection.settings_dict
    print(f"   📊 Configuration Django réelle:")
    print(f"      Database: {db_config.get('NAME', 'N/A')}")
    print(f"      Host: {db_config.get('HOST', 'N/A')}")
    print(f"      User: {db_config.get('USER', 'N/A')}")
    print(f"      Port: {db_config.get('PORT', 'N/A')}")
    
    # Vérifier quelle base de données est utilisée
    actual_db = db_config.get('NAME', '')
    if actual_db != db_name:
        print(f"\n   ⚠️  ATTENTION : Django utilise la base '{actual_db}' au lieu de '{db_name}'")
        print(f"   ℹ️  Cela peut être dû à MYSQL_URL qui écrase MYSQLDATABASE")
    
except Exception as e:
    print(f"   ⚠️  Erreur lors de la vérification: {e}")

# Étape 5 : Lister les tables créées
print(f"\n🔧 Étape 5 : Liste des tables créées...")
try:
    with connection.cursor() as cursor:
        # Afficher la base de données actuelle
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        print(f"   📊 Base de données actuelle: {current_db}")
        
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        if tables:
            print(f"   ✅ {len(tables)} table(s) trouvée(s):")
            for table in tables:
                print(f"      - {table}")
        else:
            print(f"   ⚠️  Aucune table trouvée dans la base '{current_db}'")
            print(f"   ℹ️  Vérifiez que vous regardez la bonne base de données dans Railway")
except Exception as e:
    print(f"   ⚠️  Erreur lors de la liste des tables: {e}")

print("\n" + "=" * 60)
print("✅ TERMINÉ")
print("=" * 60)
