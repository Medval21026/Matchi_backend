# 🗄️ Guide des Migrations Django vers MySQL sur Railway

## ✅ Configuration automatique (déjà en place)

Votre `Procfile` contient déjà :
```
release: python manage.py migrate --noinput
web: gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT
```

Railway exécutera automatiquement les migrations avant chaque déploiement grâce à la phase `release`.

## 🔧 Méthode 1 : Migrations automatiques (Recommandé)

Les migrations s'exécutent automatiquement à chaque déploiement. Vérifiez dans les logs de déploiement que vous voyez :
```
Running release command...
Operations to perform:
  Apply all migrations: ...
```

## 🛠️ Méthode 2 : Migrations manuelles via Railway CLI

### Installation de Railway CLI

```bash
# Windows (PowerShell)
iwr https://railway.app/install.sh | iex

# Ou via npm
npm i -g @railway/cli
```

### Connexion et exécution des migrations

```bash
# 1. Se connecter à Railway
railway login

# 2. Lier votre projet
railway link

# 3. Exécuter les migrations
railway run python manage.py migrate
```

## 🌐 Méthode 3 : Migrations via l'interface Railway

1. **Allez dans votre service "Matchi_backend"**
2. **Cliquez sur l'onglet "Settings"**
3. **Trouvez la section "Deploy"**
4. **Ajoutez une commande de build ou utilisez le terminal**

OU utilisez le **Terminal** dans Railway :
1. Allez dans votre service
2. Cliquez sur "Terminal" (si disponible)
3. Exécutez : `python manage.py migrate`

## 📝 Méthode 4 : Créer un script de migration

Créez un fichier `migrate.sh` :

```bash
#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Puis dans `railway.json`, ajoutez :

```json
{
  "deploy": {
    "startCommand": "bash migrate.sh && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT"
  }
}
```

## 🔍 Vérifier que les migrations sont appliquées

### Via Railway CLI :
```bash
railway run python manage.py showmigrations
```

### Via l'interface Railway :
1. Utilisez le terminal Railway
2. Exécutez : `python manage.py showmigrations`

## ⚠️ Important

1. **Première migration** : Assurez-vous que toutes les migrations existantes sont dans le repo
2. **Variables d'environnement** : Les variables MySQL doivent être configurées AVANT les migrations
3. **Base de données vide** : Si c'est une nouvelle base, les migrations créeront toutes les tables
4. **Base existante** : Si vous avez déjà des données, faites attention aux conflits

## 🚨 En cas d'erreur

Si les migrations échouent :

1. **Vérifiez les variables MySQL** dans Railway
2. **Vérifiez les logs** de déploiement
3. **Testez la connexion** :
   ```bash
   railway run python manage.py dbshell
   ```

## 📋 Checklist avant migration

- [ ] Variables MySQL configurées sur Railway
- [ ] `pymysql` dans `requirements.txt` ✅
- [ ] `Procfile` avec commande `release` ✅
- [ ] Toutes les migrations sont dans le repo
- [ ] Base de données MySQL accessible

## 🎯 Commandes utiles

```bash
# Voir l'état des migrations
python manage.py showmigrations

# Créer une nouvelle migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir les migrations en attente
python manage.py migrate --plan

# Rollback (attention !)
python manage.py migrate <app_name> <migration_number>
```
