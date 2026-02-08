#!/bin/bash
# Script de démarrage pour Railway
# Exécute les migrations puis démarre gunicorn

echo "=========================================="
echo "DÉMARRAGE DU SERVICE DJANGO"
echo "=========================================="

# Étape 1 : Créer la base de données et exécuter les migrations
echo ""
echo "🔧 Étape 1 : Création de la base de données et migrations..."
if python creer_database_et_migrer.py; then
    echo "✅ Migrations terminées avec succès"
else
    echo "❌ ERREUR : Les migrations ont échoué"
    echo "Le service ne démarrera pas sans migrations réussies"
    exit 1
fi

# Étape 2 : Démarrer gunicorn
echo ""
echo "🚀 Étape 2 : Démarrage de Gunicorn..."
exec gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT
