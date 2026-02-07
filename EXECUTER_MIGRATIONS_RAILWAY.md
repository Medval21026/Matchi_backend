# 🚀 Exécuter les Migrations Django sur Railway

## ⚠️ Problème actuel

Les migrations Django ne sont **pas appliquées** sur Railway. Les tables `reservations_*` n'existent pas encore dans votre base MySQL.

## ✅ Solution : Exécuter les migrations manuellement

### Méthode 1 : Via Railway CLI (Recommandé)

#### 1. Installer Railway CLI

```bash
# Windows (PowerShell)
npm i -g @railway/cli

# OU via winget
winget install Railway.Railway
```

#### 2. Se connecter à Railway

```bash
railway login
```

#### 3. Lier votre projet

```bash
cd C:\Users\HP\Desktop\matchi_web_admin
railway link
```

Sélectionnez votre projet `refreshing-dream` et le service `Matchi_backend`.

#### 4. Vérifier les variables d'environnement

```bash
railway variables
```

Assurez-vous que ces variables sont configurées :
- `MYSQLDATABASE=cite`
- `MYSQLUSER=root`
- `MYSQLPASSWORD=<votre_mot_de_passe>`
- `MYSQLHOST=<host_railway>`
- `MYSQLPORT=3306`

#### 5. Exécuter les migrations

```bash
railway run python manage.py migrate
```

#### 6. Vérifier que les migrations sont appliquées

```bash
railway run python manage.py showmigrations
```

Vous devriez voir :
```
reservations
 [X] 0001_initial
```

### Méthode 2 : Via l'interface Railway (Terminal)

1. **Allez dans votre service "Matchi_backend"** sur Railway
2. **Cliquez sur l'onglet "Settings"**
3. **Trouvez la section "Deploy"** ou **"Terminal"**
4. **Si un terminal est disponible**, exécutez :
   ```bash
   python manage.py migrate
   ```

### Méthode 3 : Forcer les migrations dans le startCommand

Modifiez `railway.json` pour forcer les migrations à chaque démarrage :

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Puis commitez et poussez :
```bash
git add railway.json
git commit -m "Force migrations on startup"
git push
```

## 🔍 Vérifier les tables créées

Après avoir exécuté les migrations, allez dans MySQL Railway → Database → Tables.

Vous devriez voir les nouvelles tables Django :
- ✅ `reservations_client`
- ✅ `reservations_terrains`
- ✅ `reservations_joueurs`
- ✅ `reservations_reservations`
- ✅ `reservations_indisponibilites`
- ✅ `django_migrations`
- ✅ `django_session`
- ✅ Et toutes les autres tables Django...

## 🚨 En cas d'erreur

### Erreur : "ModuleNotFoundError: No module named 'mysql.connector'"

Solution : Vérifiez que `mysql-connector-python==8.3.0` est dans `requirements.txt`

### Erreur : "Access denied for user"

Solution : Vérifiez les variables MySQL dans Railway (MYSQLUSER, MYSQLPASSWORD, MYSQLHOST)

### Erreur : "Unknown database 'cite'"

Solution : Vérifiez que `MYSQLDATABASE=cite` est correctement configuré

## 📋 Checklist

- [ ] Railway CLI installé
- [ ] Connecté à Railway (`railway login`)
- [ ] Projet lié (`railway link`)
- [ ] Variables MySQL configurées
- [ ] Migrations exécutées (`railway run python manage.py migrate`)
- [ ] Tables Django visibles dans MySQL Railway

## 🎯 Commandes utiles Railway CLI

```bash
# Voir les logs en temps réel
railway logs

# Voir les variables d'environnement
railway variables

# Exécuter une commande dans le conteneur
railway run <commande>

# Ouvrir un shell interactif
railway shell

# Voir l'état du service
railway status
```
