# 🔍 Pourquoi les Migrations ne se Font Pas

## ⚠️ Problème Identifié

D'après votre configuration Railway, voici pourquoi les migrations ne s'exécutent pas :

### 1. **Conflit entre `Procfile` et `railway.json`**

Vous avez **deux configurations** pour les migrations :
- `Procfile` : `release: python manage.py migrate --noinput`
- `railway.json` : `startCommand: python manage.py migrate --noinput && gunicorn...`

Railway peut utiliser l'un ou l'autre, ce qui crée une confusion.

### 2. **Nom des Variables d'Environnement**

Sur Railway, vous avez `MYSQL_DATABASE` (avec underscore), mais Django cherche d'abord `MYSQLDATABASE` (sans underscore).

**Bonne nouvelle** : Votre code a un fallback qui devrait fonctionner :
```python
'NAME': os.getenv('MYSQLDATABASE', os.getenv('MYSQL_DATABASE', 'cite')),
```

### 3. **Les Migrations Échouent Silencieusement**

Si les migrations échouent (erreur de connexion, base inexistante, etc.), Railway peut redémarrer le service sans créer les tables.

## ✅ Solution : Forcer les Migrations

### Option 1 : Utiliser uniquement `railway.json` (Recommandé)

Modifiez `railway.json` pour être plus explicite :

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput || true && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2 : Créer un Script de Migration

Créez un fichier `migrate.sh` :

```bash
#!/bin/bash
set -e
echo "Starting migrations..."
python manage.py migrate --noinput
echo "Migrations completed!"
```

Puis modifiez `railway.json` :

```json
{
  "deploy": {
    "startCommand": "chmod +x migrate.sh && ./migrate.sh && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT"
  }
}
```

### Option 3 : Vérifier les Variables sur Railway

**IMPORTANT** : Assurez-vous que ces variables existent dans votre service `Matchi_backend` :

1. Allez dans `Matchi_backend` → "Variables"
2. Vérifiez que vous avez :
   - `MYSQLDATABASE=cite` (ou `MYSQL_DATABASE=cite`)
   - `MYSQLUSER=root`
   - `MYSQLPASSWORD=lpQPTCliNnBaGBUFJsPMrJVFvFxyaCic`
   - `MYSQLHOST=<host_railway>` (probablement `mysql.railway.internal` ou l'host interne)
   - `MYSQLPORT=3306`

3. **Si `MYSQLHOST` n'est pas configuré**, allez dans le service **MySQL** → "Variables" et copiez la valeur de `MYSQLHOST`

## 🔍 Diagnostic : Vérifier les Logs

1. Allez dans `Matchi_backend` → "Logs" ou "Deploy Logs"
2. Cherchez ces messages :
   - ✅ `Running migrations...` → Les migrations s'exécutent
   - ✅ `Operations to perform: Apply all migrations: reservations` → Les migrations sont en cours
   - ❌ `No migrations to apply` → Les migrations sont déjà marquées comme appliquées (mais les tables n'existent pas)
   - ❌ `Unknown MySQL server host` → Problème de connexion
   - ❌ `Access denied` → Problème d'authentification
   - ❌ `Unknown database 'cite'` → La base n'existe pas

## 🚀 Solution Rapide : Forcer les Migrations

Si les migrations sont marquées comme appliquées mais que les tables n'existent pas :

1. **Supprimez la table `django_migrations`** (si elle existe) :
   ```sql
   USE cite;
   DROP TABLE IF EXISTS django_migrations;
   ```

2. **Redéployez le service** pour forcer les migrations

OU

1. **Réinitialisez les migrations** via Railway (si terminal disponible) :
   ```bash
   python manage.py migrate reservations zero
   python manage.py migrate
   ```

## 📋 Checklist de Vérification

- [ ] Variables MySQL configurées sur Railway (`MYSQLDATABASE` ou `MYSQL_DATABASE`)
- [ ] `MYSQLHOST` est configuré (vérifiez dans le service MySQL)
- [ ] Base de données `cite` existe dans MySQL Railway
- [ ] `railway.json` contient la commande de migration
- [ ] Les logs montrent "Running migrations..."
- [ ] Les tables `reservations_*` existent dans MySQL

## 🎯 Action Immédiate

1. **Vérifiez les variables** dans `Matchi_backend` → "Variables"
2. **Vérifiez les logs** dans `Matchi_backend` → "Logs"
3. **Redéployez** le service pour forcer l'exécution des migrations
