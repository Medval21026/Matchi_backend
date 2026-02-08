# Solution finale pour les migrations sur Railway

## Problème résolu

Railway avec Railpack **ignore** le `releaseCommand` dans `railway.json`. La solution est d'utiliser un **script bash** qui exécute les migrations **avant** de démarrer gunicorn.

## Solution implémentée

### 1. Script bash `start.sh`

Ce script :
- Exécute `creer_database_et_migrer.py` (crée la DB + migrations)
- Vérifie que les migrations ont réussi
- Démarre gunicorn seulement si les migrations réussissent

### 2. Configuration Railway

**`railway.json` :**
```json
{
  "deploy": {
    "startCommand": "bash start.sh"
  }
}
```

**`Procfile` :**
```
web: bash start.sh
```

## Ordre d'exécution

1. **Build** : Construction de l'image Docker
2. **Start** : Exécution de `start.sh`
   - Création de la base de données `cite` (si elle n'existe pas)
   - Exécution des migrations Django
   - Démarrage de gunicorn (seulement si les migrations réussissent)

## Avantages de cette approche

✅ **Garantit l'exécution** : Le script s'exécute à chaque démarrage du conteneur
✅ **Visible dans les logs** : Tous les messages apparaissent dans les Deploy Logs
✅ **Fiable** : Si les migrations échouent, le service ne démarre pas
✅ **Compatible** : Fonctionne avec Railpack et Nixpacks

## Prochaines étapes

### 1. Commiter et pousser

```powershell
git add .
git commit -m "Fix: Utiliser script bash pour exécuter migrations avant gunicorn"
git push
```

### 2. Vérifier les logs

Après le déploiement, allez sur Railway → Matchi_backend → Deploy Logs

Vous devriez voir :
```
==========================================
DÉMARRAGE DU SERVICE DJANGO
==========================================

🔧 Étape 1 : Création de la base de données et migrations...
============================================================
CRÉATION DE LA BASE DE DONNÉES ET MIGRATIONS
============================================================

📊 Configuration:
   Host: mysql-9tby.railway.internal
   User: root
   Port: 3306
   Database: cite

🔧 Étape 1 : Création de la base de données 'cite'...
   ✅ Base de données 'cite' créée ou déjà existante
   ✅ Base de données 'cite' vérifiée

🔧 Étape 2 : Exécution des migrations...
   Operations to perform:
     Apply all migrations: ...
   ✅ Migrations exécutées avec succès

✅ Migrations terminées avec succès

🚀 Étape 2 : Démarrage de Gunicorn...
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
```

### 3. Vérifier les tables

Allez sur Railway → MySQL-9TbY → Database → Data

Vous devriez voir les tables Django au lieu de "You have no tables".

## Dépannage

### Si les migrations ne s'exécutent toujours pas

1. **Vérifiez que `start.sh` est dans le repo** :
   ```powershell
   git ls-files | grep start.sh
   ```

2. **Vérifiez les logs complets** :
   - Railway → Matchi_backend → Deploy Logs
   - Cherchez les messages du script

3. **Vérifiez les variables d'environnement** :
   - `MYSQLHOST` doit être `mysql-9tby.railway.internal`
   - `MYSQLDATABASE` doit être `cite`
   - `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLPORT` doivent être corrects

### Si vous voyez "bash: start.sh: No such file or directory"

Le fichier n'est pas dans le repo. Vérifiez :
```powershell
git status
git add start.sh
git commit -m "Add start.sh script"
git push
```

### Si les migrations échouent

Les logs afficheront l'erreur exacte. Causes communes :
- Base de données n'existe pas et ne peut pas être créée
- Variables d'environnement incorrectes
- Problème de connexion à MySQL
- Erreur dans les fichiers de migration

## Fichiers modifiés

1. ✅ `start.sh` : Nouveau script bash pour démarrer le service
2. ✅ `railway.json` : Utilise `bash start.sh` comme `startCommand`
3. ✅ `Procfile` : Utilise `bash start.sh` comme commande `web`
4. ✅ `creer_database_et_migrer.py` : Amélioré pour gérer les erreurs

## Test local (optionnel)

Pour tester le script localement (si vous avez MySQL) :

```powershell
# Créer un .env avec les bonnes variables
# Puis exécuter :
bash start.sh
```
