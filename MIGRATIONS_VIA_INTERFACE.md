# 🚀 Exécuter les Migrations via l'Interface Railway

## ✅ Méthode : Via l'Interface Web Railway

Puisque Railway CLI nécessite une authentification interactive, nous allons utiliser l'interface web Railway.

### Option 1 : Via le Terminal Railway (Recommandé)

1. **Allez sur Railway** : https://railway.com
2. **Sélectionnez votre projet** : `refreshing-dream`
3. **Cliquez sur le service** : `Matchi_backend`
4. **Allez dans l'onglet "Settings"**
5. **Trouvez la section "Deploy"** ou **"Terminal"**
6. **Si un terminal est disponible**, cliquez dessus
7. **Exécutez les commandes suivantes** :

```bash
# Vérifier les variables d'environnement
env | grep MYSQL

# Exécuter les migrations
python manage.py migrate

# Vérifier que les migrations sont appliquées
python manage.py showmigrations
```

### Option 2 : Forcer les migrations au démarrage

Les migrations sont déjà configurées dans `railway.json` pour s'exécuter automatiquement au démarrage. 

**Vérifiez que les variables MySQL sont configurées sur Railway :**

1. **Allez dans votre service "Matchi_backend"**
2. **Onglet "Variables"**
3. **Vérifiez que ces variables existent :**
   - `MYSQLDATABASE=cite`
   - `MYSQLUSER=root`
   - `MYSQLPASSWORD=lpQPTCliNnBaGBUFJsPMrJVFvFxyaCic`
   - `MYSQLHOST=mysql.railway.internal` (ou l'host interne Railway)
   - `MYSQLPORT=3306`

4. **Redéployez le service** pour que les migrations s'exécutent automatiquement

### Option 3 : Créer un script de migration

Créez un fichier `migrate.sh` à la racine du projet :

```bash
#!/bin/bash
python manage.py migrate --noinput
```

Puis modifiez `railway.json` :

```json
{
  "deploy": {
    "startCommand": "bash migrate.sh && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT"
  }
}
```

## 🔍 Vérifier les migrations

Après avoir exécuté les migrations, allez dans MySQL Railway → Database → Tables.

Vous devriez voir les nouvelles tables Django :
- ✅ `reservations_client`
- ✅ `reservations_terrains`
- ✅ `reservations_joueurs`
- ✅ `django_migrations`
- ✅ etc.

## 🚨 Si les migrations ne s'exécutent pas

1. **Vérifiez les logs de déploiement** dans Railway
2. **Vérifiez que la base de données `cite` existe** dans MySQL Railway
3. **Vérifiez les variables d'environnement** MySQL
4. **Vérifiez que `mysql-connector-python` est dans `requirements.txt`**

## 📝 Note

Le fichier `.env` local n'est pas utilisé sur Railway. Railway utilise les variables d'environnement configurées dans l'interface web.
